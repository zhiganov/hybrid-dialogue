# Hybrid Dialogue

Open tools for **asynchronous and hybrid group conversation with AI** — built for Ben Roberts' Hybrid Conversation Toolkit inquiry (July 2026).

Most async tools treat a conversation as a synchronous one stretched over time: contributions stack up by timestamp, and whoever arrives late can only append to the end. This inquiry asks what becomes possible when we design for what asynchronicity actually offers — and uses AI as an *amplifier* of human-to-human dialogue, not a replacement for it. The tools here are shaped in that spirit.

## The arc

The inquiry runs as four beats:

1. **EXPRESS** — people share what draws them (a short survey).
2. **MAP** — responses become a set of conversation invitations, shown as a field.
3. **DROP INTO** — people opt into the conversations that pull them.
4. **HARVEST** — each conversation produces something worth carrying forward.

## What's in this repo

| Path | Beat | What it is | Status |
| --- | --- | --- | --- |
| [`invitation-generator/`](./invitation-generator/) | MAP | Reads the participant survey and proposes a right-sized, grounded set of conversation invitations + people recommendations, with Kumu-ready output | ✅ Built |
| [`docs/plans/2026-06-27-node-room-design.md`](./docs/plans/2026-06-27-node-room-design.md) | DROP INTO | Spec for a small-group live "node room" with Claude as facilitator, replacing the bare per-conversation Google Doc | 📝 Spec |

## The invitation generator

It turns survey responses into conversations that go beyond the obvious topics: a genuine *tension* in the group, at least one *process* conversation about the inquiry itself, and *relational* "who-should-meet-whom" pairings — each grounded in what people actually wrote, with recommended participants and archetypes worth inviting. The result is a readable brief plus Kumu-ready spreadsheets.

**Most people never run this.** It's not an app participants install — one person comfortable with a terminal runs it once and shares the result; everyone else simply receives the set of conversations. If that's you, the [tool's README](./invitation-generator/README.md) has the steps and the editable prompt.

## Privacy

Survey responses and voice notes are personal data and never belong in a public repo. Real input lives in a gitignored `data/` folder, generated output is gitignored too, and only contact-free substance fields are ever sent to the model. The included `sample-input.csv` is synthetic.

## Credits

Convened by **Ben Roberts** (Conversation Collaborative). Tooling contributed by Artem Zhiganov.

## License

MIT — see [`LICENSE`](./LICENSE).
