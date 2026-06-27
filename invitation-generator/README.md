# Invitation generator (Beat 2)

Turns survey responses into a right-sized, grounded set of **conversation invitations** plus **people recommendations**, for Ben Roberts' Hybrid Conversation Toolkit inquiry.

This is Beat 2 of the arc **EXPRESS → MAP → DROP INTO → HARVEST**: it maps the survey (EXPRESS) into the set of conversations people then opt into. Output is a **draft for human curation**, not a final answer — the point is to collaborate with Claude, not hand the decision to it.

## What it produces

For a survey CSV it writes (to `output/`):

- `invitations-<date>.md` — readable brief: each invitation with its framing, what it's grounded in, recommended participants (+ why), and archetypes of people worth inviting who aren't here yet.
- `invitations-<date>.json` — the raw structured result.
- `kumu-elements-<date>.csv` — `Engagement Node` rows for the Kumu Elements sheet.
- `kumu-connections-<date>.csv` — `Person → Node` rows of type `Suggested` for the Kumu Connections sheet.

## What the prompt asks for

The full prompt is in [`prompt.md`](./prompt.md) (edit it freely). In short, it pushes Claude past naive topic-clustering toward:

- **Grounded** invitations traceable to specific things specific people said.
- A **mix of conversation types**, not just content: `content`, `tension` (a real disagreement between participants), `process` (at least one conversation about the inquiry itself), and `relational` (who-meets-whom).
- **Right-sizing** — enough to give choice, few enough not to fragment a small group.
- **Latent threads**, not only the loudest interests.
- People recommendations on **fit and complementarity**, plus archetypes to invite.

## Run it

```sh
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # or put it in a .env file (see --env-file)

# try the synthetic sample first
python generate.py --input sample-input.csv --num 4

# real run
python generate.py --input /path/to/elements-people.csv --num 6
```

Options: `--num` target invitation count (default 6), `--model` (default `claude-opus-4-8`), `--out` output dir, `--env-file` fallback file holding `ANTHROPIC_API_KEY=`.

## Privacy

The survey contains participants' words and contact details. **Do not commit real survey data or generated `output/` into this public repo** — `output/` is gitignored, and the included `sample-input.csv` is synthetic. Only contact-free substance fields are sent to the model.
