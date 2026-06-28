#!/usr/bin/env python3
"""Provision one node-room room per invitation, idempotently.

Reads an invitations-*.json, creates a node-room room per invitation via
POST {base}/api/rooms, and writes a private mapping rooms-<date>.json keyed
by slug(title). Re-runs reuse existing rooms (no duplicates). The mapping
holds facilitator tokens and is gitignored; only room_url is public.

Usage:
  python create_rooms.py --input output/invitations-2026-06-27.json \
      --base https://node-room-web-production.up.railway.app
"""
import argparse
import glob
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent


def slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60] or "conversation"


def facilitation_brief(inv: dict) -> str:
    framing = inv.get("framing", "").strip()
    return (
        f"This is an asynchronous small-group conversation. {framing}\n\n"
        "Help the group surface questions, stories, challenges, and syntheses, "
        "and draw the threads toward a harvestable shared understanding. Stay "
        "quiet unless asked or unless a weave will genuinely help."
    )


def create_room(base: str, inv: dict) -> dict:
    payload = json.dumps(
        {
            "nodeTitle": inv.get("title", ""),
            "nodeDescription": inv.get("framing", ""),
            "facilitationPrompt": facilitation_brief(inv),
            "listed": True,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base.rstrip('/')}/api/rooms",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def provision(invs, base, mapping, create_fn):
    base = base.rstrip("/")
    mapping["base_url"] = base
    mapping.setdefault("rooms", {})
    for inv in invs:
        title = inv.get("title", "")
        key = slug(title)
        if key in mapping["rooms"]:
            print(f"skip (exists): {title}")
            continue
        try:
            res = create_fn(base, inv)
        except Exception as ex:  # noqa: BLE001 - log and continue per design
            print(f"FAILED: {title} ({ex})", file=sys.stderr)
            continue
        rid, tok = res["id"], res["facilitatorToken"]
        mapping["rooms"][key] = {
            "title": title,
            "room_id": rid,
            "facilitator_token": tok,
            "room_url": f"{base}/room/{rid}",
            "manage_url": f"{base}/room/{rid}/manage?key={tok}",
        }
        print(f"created: {title} -> {base}/room/{rid}")
    return mapping


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", help="invitations-*.json (defaults to newest in ./output)")
    ap.add_argument("--base", default="https://node-room-web-production.up.railway.app")
    ap.add_argument("--out", default=str(HERE / "output"))
    args = ap.parse_args()

    inp = args.input
    if not inp:
        cands = sorted(glob.glob(str(HERE / "output" / "invitations-*.json")))
        if not cands:
            raise SystemExit("No invitations-*.json found; pass --input")
        inp = cands[-1]

    data = json.loads(pathlib.Path(inp).read_text(encoding="utf-8"))
    invs = data.get("invitations", [])
    m = re.search(r"(\d{4}-\d{2}-\d{2})", pathlib.Path(inp).name)
    date_str = m.group(1) if m else "rooms"

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    mapping_path = out / f"rooms-{date_str}.json"
    mapping = {"base_url": args.base, "rooms": {}}
    if mapping_path.exists():
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))

    provision(invs, args.base, mapping, create_room)
    mapping_path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(f"Wrote {mapping_path}")


if __name__ == "__main__":
    main()
