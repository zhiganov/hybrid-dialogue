import Link from "next/link";
import { listRooms } from "@/lib/rooms";

export const dynamic = "force-dynamic";

function timeAgo(iso: string | null): string {
  if (!iso) return "no posts yet";
  const secs = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (secs < 45) return "just now";
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

export default async function Home() {
  const rooms = await listRooms();
  return (
    <main className="page">
      <header className="page-head">
        <h1 className="title">Hybrid Dialogue</h1>
        <p className="lede">
          A small group and Claude think together in writing, over days. Enter a
          conversation below, or start one of your own.
        </p>
      </header>

      {rooms.length === 0 ? (
        <p className="empty">No conversations yet. You could open the first one.</p>
      ) : (
        <ol className="thread" aria-label="Open conversations">
          {rooms.map((r) => (
            <li className="entry" key={r.id}>
              <p className="entry-meta">
                <span>
                  {r.participantCount} {r.participantCount === 1 ? "person" : "people"}
                </span>
                <span className="entry-dot" aria-hidden="true">
                  &middot;
                </span>
                <span>{timeAgo(r.lastActivityAt)}</span>
              </p>
              <h2 className="section-title">
                <Link className="room-link" href={`/room/${r.id}`}>
                  {r.nodeTitle}
                </Link>
              </h2>
              <p className="entry-body">{r.nodeDescription}</p>
            </li>
          ))}
        </ol>
      )}
    </main>
  );
}
