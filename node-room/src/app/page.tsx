import Link from "next/link";

export default function Home() {
  return (
    <main className="welcome">
      <div className="page-head">
        <h1 className="title">Hybrid Dialogue</h1>
        <p className="lede">
          A small group and Claude think together in writing, over days. Open a
          room link to join a conversation, or start one of your own.
        </p>
      </div>
      <p>
        <Link className="link" href="/create">
          Create a conversation room
        </Link>
      </p>
    </main>
  );
}
