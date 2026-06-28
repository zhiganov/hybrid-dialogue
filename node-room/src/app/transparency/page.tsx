import Link from "next/link";
import { STANCE, MODELS, INSTRUCTIONS } from "@/lib/claude";

const SOURCE =
  "https://github.com/zhiganov/hybrid-dialogue/blob/main/node-room/src/lib/claude.ts";

const ROLES: { key: keyof typeof MODELS; label: string; what: string }[] = [
  { key: "openingFrame", label: "Opening frame", what: "Welcomes people when a room opens." },
  { key: "reply", label: "Reply to @claude", what: "Answers when someone writes @claude." },
  { key: "weave", label: "Weave", what: "Connects recent contributions, on a schedule or when the facilitator asks." },
  { key: "harvest", label: "Harvest", what: "Distills the conversation into a draft to carry forward." },
];

export default function Transparency() {
  return (
    <main className="page">
      <header className="page-head">
        <h1 className="title">Under the hood</h1>
        <p className="lede">
          What the AI in these rooms is, and exactly what it is told to do. It is here to
          amplify human dialogue, not to speak for anyone.
        </p>
      </header>

      <section className="panel">
        <h2 className="section-title">Which model does what</h2>
        {ROLES.map((r) => (
          <p className="entry-meta" key={r.key}>
            <span className="entry-author">{r.label}</span>
            <span className="entry-dot" aria-hidden="true">
              &middot;
            </span>
            <span>{MODELS[r.key]}</span>
            <span className="entry-dot" aria-hidden="true">
              &middot;
            </span>
            <span>{r.what}</span>
          </p>
        ))}
        <p className="field-hint">
          The models run on the host&apos;s API key. Source:{" "}
          <a className="link" href={SOURCE} target="_blank" rel="noopener">
            claude.ts
          </a>
          .
        </p>
      </section>

      <section className="panel">
        <h2 className="section-title">The facilitator&apos;s stance (system prompt)</h2>
        <p className="entry-body">{STANCE}</p>
      </section>

      <section className="panel">
        <h2 className="section-title">What it is told, per moment</h2>
        {ROLES.map((r) => (
          <div className="link-block" key={r.key}>
            <span className="field-label">{r.label}</span>
            <p className="entry-body">{INSTRUCTIONS[r.key]}</p>
          </div>
        ))}
        <p className="field-hint">
          These prompts live in{" "}
          <a className="link" href={SOURCE} target="_blank" rel="noopener">
            node-room/src/lib/claude.ts
          </a>
          . To change them, edit that file and open a pull request; the change deploys on merge.
        </p>
      </section>

      <p>
        <Link className="link" href="/">
          Back to the conversations
        </Link>
      </p>
    </main>
  );
}
