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

export function RoomClient(props: {
  roomId: string;
  nodeTitle: string;
  nodeDescription: string;
}) {
  const { roomId } = props;
  const [token, setToken] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [tag, setTag] = useState<ContributionTag | "">("");
  const [sending, setSending] = useState(false);
  const sinceRef = useRef(0);

  useEffect(() => {
    setToken(localStorage.getItem(tokenKey(roomId)));
  }, [roomId]);

  const poll = useCallback(async () => {
    const res = await fetch(`/api/rooms/${roomId}/messages?since=${sinceRef.current}`);
    if (!res.ok) return;
    const data = (await res.json()) as { messages: UiMessage[] };
    if (data.messages.length) {
      sinceRef.current = data.messages[data.messages.length - 1].id;
      setMessages((prev) => [...prev, ...data.messages]);
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
    const res = await fetch(`/api/rooms/${roomId}/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ displayName: name.trim() }),
    });
    if (!res.ok) return;
    const data = (await res.json()) as { participantToken: string };
    localStorage.setItem(tokenKey(roomId), data.participantToken);
    setToken(data.participantToken);
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim() || !token) return;
    setSending(true);
    try {
      const res = await fetch(`/api/rooms/${roomId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ participantToken: token, body: draft.trim(), tag: tag || undefined }),
      });
      if (res.ok) {
        setDraft("");
        setTag("");
        await poll();
      }
    } finally {
      setSending(false);
    }
  }

  if (!token) {
    return (
      <main style={{ maxWidth: 640, margin: "0 auto", padding: 24 }}>
        <h1>{props.nodeTitle}</h1>
        <p>{props.nodeDescription}</p>
        <form onSubmit={join}>
          <label>
            Your name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <button type="submit">Enter the conversation</button>
        </form>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <h1>{props.nodeTitle}</h1>
      <p>{props.nodeDescription}</p>

      <ol style={{ listStyle: "none", padding: 0 }}>
        {messages.map((m) => (
          <li key={m.id} style={{ margin: "16px 0" }}>
            <strong>{m.authorType === "claude" ? "Facilitator" : m.authorName}</strong>
            {m.contributionTag ? <em> ({m.contributionTag})</em> : null}
            <div style={{ whiteSpace: "pre-wrap" }}>{m.body}</div>
          </li>
        ))}
      </ol>

      <form onSubmit={send}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Add to the conversation (use @claude to ask the facilitator)"
          rows={3}
          required
        />
        <div>
          <select value={tag} onChange={(e) => setTag(e.target.value as ContributionTag | "")}>
            <option value="">No tag</option>
            {CONTRIBUTION_TAGS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <button type="submit" disabled={sending}>
            {sending ? "Posting" : "Post"}
          </button>
        </div>
      </form>
    </main>
  );
}
