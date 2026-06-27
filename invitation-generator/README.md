# Invitation generator

**The problem.** The inquiry gathered 16 people who want to explore better tools for online conversation. But 16 people can't have one good conversation — it has to split into a handful of smaller, focused ones. Someone has to decide *which* conversations are worth having and *who* belongs in each. Done by hand, or with a lazy prompt, you get generic buckets ("AI and community", "the future of dialogue") and you miss the interesting stuff.

**What this does.** It reads every participant's survey answers — what draws them, their doubts, what they want to build, the methods they use — and proposes a small, right-sized set of *specific* conversations, each grounded in what people actually wrote, with recommended participants and archetypes of people worth inviting who aren't here yet.

It deliberately goes past topic-clustering to include:

- a real **tension** in the group — a genuine disagreement, named with its poles;
- at least one **process** conversation about the inquiry itself (how to run it, what success looks like) — the kind a naive list always skips;
- **relational** "who-should-meet-whom" pairings;
- and **latent threads** — quiet signals only one or two people raised.

**Example.** Instead of a bland "AI ethics" topic, a run produced *"Can we build with AI without feeding the machine that extracts us?"* — grounded in one person's words about extraction, another's question about data training, and a third's skepticism — with five suggested participants and a note on who to recruit.

**It's a draft, not a verdict.** The AI does the legwork — reading, clustering, matchmaking — and hands the convener something to edit instead of a blank page. The human decides what matters.

## How it fits the inquiry

The inquiry runs as an arc: people **express** (a survey) → the responses are **mapped** into this set of conversations → people **drop into** the ones that pull them (each becomes a node on a Kumu map and a WhatsApp group) → each conversation **harvests** something worth keeping. This tool is the *map* step.

## What it produces

For a survey CSV it writes (to `output/`):

- `invitations-<date>.md` — readable brief: each conversation with its framing, what it's grounded in, recommended participants (+ why), and archetypes worth inviting who aren't here yet.
- `invitations-<date>.json` — the raw structured result.
- `kumu-elements-<date>.csv` — `Engagement Node` rows for the Kumu Elements sheet.
- `kumu-connections-<date>.csv` — `Person → Node` rows of type `Suggested` for the Kumu Connections sheet.

## Read it as a web page

A long markdown brief doesn't get read. `render_html.py` turns the JSON into a single, navigable HTML page — each conversation as a card you can filter by kind, plus a lightweight **curation layer**: set each to keep / maybe / cut, uncheck people who don't fit, and a "Copy curation as Markdown" button that exports the decisions to paste back. (Following [Thariq Shihipar's HTML-over-Markdown approach](https://claude.com/blog/using-claude-code-the-unreasonable-effectiveness-of-html).)

```sh
python render_html.py --input output/invitations-<date>.json
```

It reads the existing JSON — no API call — and writes `output/invitations-<date>.html`. Open it locally, or upload the single file anywhere static (e.g. Netlify) to share a link. The reader's keep/cut/note choices are saved only in their own browser (localStorage); nothing is sent anywhere.

## The prompt

The full prompt lives in [`prompt.md`](./prompt.md) — read and edit it freely; it's the heart of the tool. It's what pushes Claude past naive topic-clustering toward grounded, mixed-type, right-sized conversations with fit-and-complementarity matchmaking.

## Running it yourself

You probably don't need to. In practice one person comfortable with a terminal runs this once and shares the result — everyone else just receives the set of conversations and never touches the code. These steps are for that person, or for anyone who wants to adapt the tool.

```sh
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # or put it in a .env file (see --env-file)

# try the synthetic sample first (no real data needed)
python generate.py --input sample-input.csv --num 4

# real run
python generate.py --input /path/to/elements-people.csv --num 6
```

Options: `--num` target invitation count (default 6), `--model` (default `claude-opus-4-8`), `--out` output dir, `--env-file` fallback file holding `ANTHROPIC_API_KEY=`.

## Privacy

The survey contains participants' words and contact details. **Do not commit real survey data or generated `output/` into this public repo** — `output/` is gitignored, and the included `sample-input.csv` is synthetic. Only contact-free substance fields are sent to the model.
