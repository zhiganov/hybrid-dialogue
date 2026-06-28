"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CONTRIBUTION_TAGS, POLL_INTERVAL_MS, type ContributionTag } from "@/lib/domain";

type UiMessage = {
  id: number;
  authorType: "human" | "claude" | "system";
  authorName: string | null;
  body: string;
  contributionTag: ContributionTag | null;
  createdAt: string;
};

function tokenKey(roomId: string) {
  return `node-room-token-${roomId}`;
}

function timeAgo(iso: string): string {
  const secs = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (secs < 45) return "just now";
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.round(hrs / 24);
  return `${days}d ago`;
}

export function RoomClient(props: {
  roomId: string;
  nodeTitle: string;
  nodeDescription: string;
}) {
  const { roomId } = props;
  const [token, setToken] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [joinError, setJoinError] = useState(false);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [draft, setDraft] = useState("");
  const [tag, setTag] = useState<ContributionTag | "">("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState(false);
  const sinceRef = useRef(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setToken(localStorage.getItem(tokenKey(roomId)));
  }, [roomId]);

  const poll = useCallback(async () => {
    const res = await fetch(`/api/rooms/${roomId}/messages?since=${sinceRef.current}`);
    if (!res.ok) return;
    const data = (await res.json()) as { messages: UiMessage[] };
    setLoaded(true);
    if (data.messages.length) {
      const maxId = Math.max(...data.messages.map((m) => m.id));
      sinceRef.current = Math.max(sinceRef.current, maxId);
      setMessages((prev) => {
        const known = new Set(prev.map((m) => m.id));
        const fresh = data.messages.filter((m) => !known.has(m.id));
        return fresh.length ? [...prev, ...fresh] : prev;
      });
    }
  }, [roomId]);

  useEffect(() => {
    void poll();
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") void poll();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [poll]);

  async function join(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setJoinError(false);
    try {
      const res = await fetch(`/api/rooms/${roomId}/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ displayName: name.trim() }),
      });
      if (!res.ok) {
        setJoinError(true);
        return;
      }
      const data = (await res.json()) as { participantToken: string };
      localStorage.setItem(tokenKey(roomId), data.participantToken);
      setToken(data.participantToken);
    } catch {
      setJoinError(true);
    }
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim() || !token) return;
    setSending(true);
    setSendError(false);
    try {
      const res = await fetch(`/api/rooms/${roomId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ participantToken: token, body: draft.trim(), tag: tag || undefined }),
      });
      if (!res.ok) {
        setSendError(true);
        return;
      }
      setDraft("");
      setTag("");
      await poll();
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    } catch {
      setSendError(true);
    } finally {
      setSending(false);
    }
  }

  if (!token) {
    return (
      <main className="welcome">
        <div className="page-head">
          <h1 className="title">{props.nodeTitle}</h1>
          <p className="lede">{props.nodeDescription}</p>
        </div>
        <form className="field" onSubmit={join}>
          <label className="field-label" htmlFor="name">
            Your name
          </label>
          <input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="How you want to appear in the room"
            autoFocus
            required
          />
          <p className="field-hint">
            Your name stays in this room. When the conversation is harvested, the
            shared map carries only its shape: the themes and how they connect,
            never names or what anyone wrote.
          </p>
          {joinError ? (
            <p className="notice notice--error" role="alert">
              Could not enter the room. Please check the link and try again.
            </p>
          ) : null}
          <div className="btn-row">
            <button className="btn btn--primary" type="submit">
              Enter the conversation
            </button>
          </div>
        </form>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="page-head">
        <h1 className="title">{props.nodeTitle}</h1>
        <p className="lede">{props.nodeDescription}</p>
      </header>

      <ol className="thread" aria-live="polite" aria-label="Conversation">
        {messages.map((m) =>
          m.authorType === "claude" ? (
            <li className="entry entry--weave" key={m.id}>
              <p className="entry-meta">
                <span className="weave-author">
                  <span className="weave-mark" aria-hidden="true">
                    &#9672;
                  </span>
                  Claude
                </span>
                <span className="entry-dot" aria-hidden="true">
                  &middot;
                </span>
                <span>{timeAgo(m.createdAt)}</span>
                <span className="entry-dot" aria-hidden="true">
                  &middot;
                </span>
                <span className="weave-label">weave</span>
              </p>
              <p className="entry-body">{m.body}</p>
            </li>
          ) : (
            <li className="entry" key={m.id}>
              <p className="entry-meta">
                <span className="entry-author">{m.authorName ?? "Someone"}</span>
                <span className="entry-dot" aria-hidden="true">
                  &middot;
                </span>
                <span>{timeAgo(m.createdAt)}</span>
                {m.contributionTag ? (
                  <span className={`tag tag--${m.contributionTag}`}>{m.contributionTag}</span>
                ) : null}
              </p>
              <p className="entry-body">{m.body}</p>
            </li>
          )
        )}
      </ol>

      {loaded && messages.length === 0 ? (
        <p className="empty">
          No one has written yet. You could be the first to add a thought.
        </p>
      ) : null}

      <form className="composer" onSubmit={send}>
        <div className="field">
          <label className="field-label" htmlFor="draft">
            Add to the conversation
          </label>
          <textarea
            id="draft"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Write a thought. Mention @claude to ask the facilitator."
            rows={3}
            required
          />
        </div>
        <div className="composer-row">
          <span className="composer-tag">
            <label className="field-label" htmlFor="tag">
              Kind
            </label>
            <select
              id="tag"
              value={tag}
              onChange={(e) => setTag(e.target.value as ContributionTag | "")}
            >
              <option value="">No tag</option>
              {CONTRIBUTION_TAGS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </span>
          <button className="btn btn--primary" type="submit" disabled={sending}>
            {sending ? "Posting" : "Post"}
          </button>
        </div>
        {sendError ? (
          <p className="notice notice--error" role="alert">
            Your message did not send. It is still here, so you can try again.
          </p>
        ) : null}
      </form>

      <div ref={bottomRef} />
    </main>
  );
}
