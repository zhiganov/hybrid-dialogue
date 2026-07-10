import Link from "next/link";
import { CONTRIBUTION_TAGS, TAG_DEFINITIONS, TAG_LABELS } from "@/lib/domain";

export default function About() {
  return (
    <main className="page">
      <header className="page-head">
        <h1 className="title">About this inquiry</h1>
        <p className="lede">
          Hybrid Dialogue is a small set of conversation rooms, made for an inquiry into
          better tools for asynchronous and hybrid conversation.
        </p>
      </header>

      <section className="panel">
        <h2 className="section-title">The inquiry</h2>
        <p className="entry-body">
          Ben Roberts convened a group of facilitators, builders, and dialogue
          practitioners to explore how small groups can think well together when they are
          not all in the room at the same time. Everyone began by answering a survey about
          what draws them, what they doubt, and what they want to build.
        </p>
      </section>

      <section className="panel">
        <h2 className="section-title">How it works</h2>
        <p className="entry-body">
          The inquiry runs as an arc. People express (the survey), the responses are
          mapped into a handful of conversation invitations, people drop into the ones
          that pull them (each becomes a room here), and each conversation is harvested
          into something worth carrying forward.
        </p>
        <p className="entry-body">
          A room is slow on purpose. You read what others have left, add one considered
          contribution, and come back over days. It is a correspondence, not a chat.
        </p>
      </section>

      <section className="panel">
        <h2 className="section-title">Claude&apos;s role</h2>
        <p className="entry-body">
          Claude is here as a quiet facilitator: it welcomes people when a room opens,
          weaves recent contributions together, answers when someone writes @claude, and
          helps distill the harvest. It is here to amplify human dialogue, not to speak
          for anyone. You can read exactly what it is told to do on the{" "}
          <Link className="link" href="/transparency">
            Under the hood
          </Link>{" "}
          page.
        </p>
      </section>

      <section className="panel">
        <h2 className="section-title">Weaving and harvesting</h2>
        <p className="entry-body">
          As a conversation grows, Claude posts a <em>weave</em>: a short note that
          connects recent contributions and draws out the threads, so newcomers can find
          their way in and the arc stays legible. It happens on its own as the room
          fills, and a conversation designer can also ask for one.
        </p>
        <p className="entry-body">
          At the end, a conversation designer writes the <em>harvest</em>: a distillation of what
          the conversation produced, to carry forward. It can be exported to a shared map
          (Kumu) that carries only the anonymized shape, the themes and how they connect,
          never names or what anyone wrote.
        </p>
      </section>

      <section className="panel">
        <h2 className="section-title">Contribution kinds</h2>
        <p className="entry-body">
          When you add a thought you can mark its kind. It is optional, and it helps
          Claude weave and the conversation designer harvest:
        </p>
        <ul className="kinds">
          {CONTRIBUTION_TAGS.map((t) => (
            <li key={t}>
              <strong>{TAG_LABELS[t]}</strong>, {TAG_DEFINITIONS[t]}.
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2 className="section-title">Privacy</h2>
        <p className="entry-body">
          Your name stays in the room you join. When a conversation is harvested, the
          shared map carries only its shape: the themes and how they connect, never names
          or what anyone wrote.
        </p>
      </section>

      <p>
        <Link className="link" href="/create">
          Start a conversation room
        </Link>
      </p>
    </main>
  );
}
