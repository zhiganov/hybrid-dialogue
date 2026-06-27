#!/usr/bin/env python3
"""
Generate conversation invitations + people recommendations from survey data.

Part of Ben Roberts' Hybrid Conversation Toolkit inquiry. This is Beat 2 of the
arc EXPRESS -> MAP -> DROP INTO -> HARVEST: it turns the survey responses (EXPRESS)
into a right-sized, grounded set of conversation invitations (MAP) that people then
opt into.

It reads the Kumu "elements / people" CSV, asks Claude to propose invitations
spanning content / tension / process / relational types -- each with recommended
current participants and archetypes worth inviting -- then writes:
  - a human-readable markdown brief (for curation)
  - the raw JSON
  - Kumu-ready CSV rows: Engagement Node elements + Person->Node "Suggested" connections

The prompt lives in prompt.md so it can be read and edited without touching code.

Usage:
  export ANTHROPIC_API_KEY=...           # or use --env-file
  python generate.py --input survey.csv --num 6
"""
import argparse
import csv
import datetime
import json
import os
import pathlib
import sys

import anthropic

HERE = pathlib.Path(__file__).parent

# Survey columns fed to the model -- substance only, no contact info / PII.
PROFILE_FIELDS = [
    "Time zone",
    "How my presence contributes to diversity",
    "What draws me to this inquiry?",
    "Doubts and reservations",
    "Specific contexts or use-cases of interest",
    "Specific design processes or methodologies of interest",
    "Software development expertise",
    "Large group dialogue expertise",
    "Interest in developing software",
    "Interest in working with Claude",
    "Is there more about the kind of conversations you would like to have?",
    "Additional input",
]

OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["invitations", "notes_for_curation"],
    "properties": {
        "invitations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "title", "type", "framing", "grounded_in",
                    "recommended_participants", "archetypes_to_invite",
                ],
                "properties": {
                    "title": {"type": "string"},
                    "type": {"type": "string",
                             "enum": ["content", "tension", "process", "relational"]},
                    "framing": {"type": "string"},
                    "grounded_in": {"type": "array", "items": {"type": "string"}},
                    "recommended_participants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["name", "why"],
                            "properties": {
                                "name": {"type": "string"},
                                "why": {"type": "string"},
                            },
                        },
                    },
                    "archetypes_to_invite": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "notes_for_curation": {"type": "string"},
    },
}


def load_api_key(env_file: str) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    p = pathlib.Path(env_file).expanduser()
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ANTHROPIC_API_KEY not set (env var or --env-file).")


def read_csv(path: str):
    people, resources = [], []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            kind = (row.get("Type") or "").strip().lower()
            if kind == "person":
                people.append(row)
            elif kind == "resource":
                resources.append(row)
    return people, resources


def format_profiles(people) -> str:
    blocks = []
    for p in people:
        name = (p.get("Label") or "").strip()
        if not name:
            continue
        lines = [f"### {name}"]
        for field in PROFILE_FIELDS:
            val = (p.get(field) or "").strip()
            if val:
                lines.append(f"- {field}: {val}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def format_resources(resources) -> str:
    out = []
    for r in resources:
        label = (r.get("Label") or "").strip()
        url = (r.get("Resource url") or "").strip()
        if label:
            out.append(f"- {label}" + (f" ({url})" if url else ""))
    return "\n".join(out)


def parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1].lstrip("json").strip() if "```" in text else text
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def get_message(client, model, system_prompt, user_msg):
    common = dict(
        model=model,
        max_tokens=32000,
        thinking={"type": "adaptive"},
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    try:
        with client.messages.stream(
            output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
            **common,
        ) as stream:
            return stream.get_final_message()
    except TypeError:
        # Older SDK without output_config -- rely on the JSON instruction in the prompt.
        with client.messages.stream(**common) as stream:
            return stream.get_final_message()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="Path to the Kumu elements/people CSV")
    ap.add_argument("--num", type=int, default=6, help="Target number of invitations (default 6)")
    ap.add_argument("--model", default="claude-opus-4-8")
    ap.add_argument("--out", default=str(HERE / "output"))
    ap.add_argument("--env-file", default=".env", help="Fallback file holding ANTHROPIC_API_KEY=")
    args = ap.parse_args()

    key = load_api_key(args.env_file)
    people, resources = read_csv(args.input)
    if not people:
        sys.exit("No Person rows found in CSV.")

    system_prompt = (HERE / "prompt.md").read_text(encoding="utf-8")
    user_msg = (
        f"There are {len(people)} participants. Aim for about {args.num} conversation "
        f"invitations (use judgement -- a few more or fewer is fine if it serves the group).\n\n"
        f"## Participants\n\n{format_profiles(people)}\n\n"
        f"## Resources participants shared\n\n{format_resources(resources) or '(none)'}\n\n"
        "Now produce the invitation set. Return ONLY a JSON object with keys "
        "\"invitations\" (array; each item: title, type one of "
        "content|tension|process|relational, framing, grounded_in [strings], "
        "recommended_participants [{name, why}], archetypes_to_invite [strings]) and "
        "\"notes_for_curation\" (string)."
    )

    client = anthropic.Anthropic(api_key=key)
    print(f"Calling {args.model} over {len(people)} participants...", file=sys.stderr)
    msg = get_message(client, args.model, system_prompt, user_msg)
    text = "".join(b.text for b in msg.content if b.type == "text")
    data = parse_json(text)

    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.date.today().isoformat()

    (outdir / f"invitations-{stamp}.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8")

    md = [
        f"# Conversation invitations (draft) -- {stamp}", "",
        f"_Generated from {len(people)} survey responses with {args.model}. "
        "A draft for human curation._", "",
    ]
    for i, inv in enumerate(data["invitations"], 1):
        md += [
            f"## {i}. {inv['title']}  `[{inv['type']}]`", "",
            inv["framing"], "",
            "**Grounded in:** " + "; ".join(inv["grounded_in"]), "",
            "**Recommended participants:**",
        ]
        md += [f"- **{rp['name']}** -- {rp['why']}" for rp in inv["recommended_participants"]]
        md += ["", "**Archetypes to invite:** " + "; ".join(inv["archetypes_to_invite"]), ""]
    md += ["---", "", "## Notes for curation", "", data["notes_for_curation"], ""]
    (outdir / f"invitations-{stamp}.md").write_text("\n".join(md), encoding="utf-8")

    with open(outdir / f"kumu-elements-{stamp}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Label", "Type"])
        for inv in data["invitations"]:
            w.writerow([inv["title"], "Engagement Node"])
    with open(outdir / f"kumu-connections-{stamp}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["From", "To", "Type"])
        for inv in data["invitations"]:
            for rp in inv["recommended_participants"]:
                w.writerow([rp["name"], inv["title"], "Suggested"])

    print(f"\nWrote {len(data['invitations'])} invitations to {outdir}\n", file=sys.stderr)
    for inv in data["invitations"]:
        print(f"  [{inv['type']:>10}] {inv['title']}  "
              f"({len(inv['recommended_participants'])} people)", file=sys.stderr)


if __name__ == "__main__":
    main()
