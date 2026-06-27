"use client";

import { useState } from "react";

export default function CreatePage() {
  const [nodeTitle, setNodeTitle] = useState("");
  const [nodeDescription, setNodeDescription] = useState("");
  const [facilitationPrompt, setFacilitationPrompt] = useState("");
  const [result, setResult] = useState<{ id: string; facilitatorToken: string } | null>(null);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch(`/api/rooms`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nodeTitle, nodeDescription, facilitationPrompt }),
    });
    if (res.ok) setResult(await res.json());
  }

  if (result) {
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    return (
      <main style={{ maxWidth: 640, margin: "0 auto", padding: 24 }}>
        <h1>Room created</h1>
        <p>Share this link with participants:</p>
        <code>{`${origin}/room/${result.id}`}</code>
        <p>Your private facilitator link (keep it to yourself):</p>
        <code>{`${origin}/room/${result.id}/manage?key=${result.facilitatorToken}`}</code>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: 24 }}>
      <h1>Create a conversation room</h1>
      <form onSubmit={create}>
        <label>
          Node title
          <input value={nodeTitle} onChange={(e) => setNodeTitle(e.target.value)} required />
        </label>
        <label>
          Description
          <textarea value={nodeDescription} onChange={(e) => setNodeDescription(e.target.value)} required />
        </label>
        <label>
          Facilitation guidance for Claude
          <textarea value={facilitationPrompt} onChange={(e) => setFacilitationPrompt(e.target.value)} />
        </label>
        <button type="submit">Create room</button>
      </form>
    </main>
  );
}
