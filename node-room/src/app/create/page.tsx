"use client";

import { useState } from "react";

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="btn btn--quiet"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        } catch {
          /* clipboard unavailable; the link is visible to copy by hand */
        }
      }}
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export default function CreatePage() {
  const [nodeTitle, setNodeTitle] = useState("");
  const [nodeDescription, setNodeDescription] = useState("");
  const [facilitationPrompt, setFacilitationPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(false);
  const [result, setResult] = useState<{ id: string; facilitatorToken: string } | null>(null);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(false);
    try {
      const res = await fetch(`/api/rooms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nodeTitle, nodeDescription, facilitationPrompt }),
      });
      if (!res.ok) {
        setError(true);
        return;
      }
      setResult(await res.json());
    } catch {
      setError(true);
    } finally {
      setSubmitting(false);
    }
  }

  if (result) {
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const participant = `${origin}/room/${result.id}`;
    const manage = `${origin}/room/${result.id}/manage?key=${result.facilitatorToken}`;
    return (
      <main className="page">
        <header className="page-head">
          <h1 className="title">Room created</h1>
          <p className="lede">Two links. Share the first; keep the second to yourself.</p>
        </header>

        <section className="link-block">
          <span className="field-label">Share with participants</span>
          <span className="field-hint">Anyone with this link can read and add to the conversation.</span>
          <span className="link-value">
            <code>{participant}</code>
            <CopyButton value={participant} />
          </span>
        </section>

        <section className="link-block">
          <span className="field-label">Your private facilitator link</span>
          <span className="field-hint">
            This holds your facilitator key. Keep it to yourself; it lets you weave, harvest, and export.
          </span>
          <span className="link-value">
            <code>{manage}</code>
            <CopyButton value={manage} />
          </span>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="page-head">
        <h1 className="title">Create a conversation room</h1>
        <p className="lede">
          Seed an engagement node. Claude posts an opening frame and facilitates quietly from there.
        </p>
      </header>

      <form className="composer" onSubmit={create}>
        <div className="field">
          <label className="field-label" htmlFor="node-title">
            Node title
          </label>
          <input
            id="node-title"
            value={nodeTitle}
            onChange={(e) => setNodeTitle(e.target.value)}
            placeholder="What does trust actually require of us?"
            required
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="node-description">
            Description
          </label>
          <textarea
            id="node-description"
            value={nodeDescription}
            onChange={(e) => setNodeDescription(e.target.value)}
            placeholder="A sentence or two on what this conversation is about."
            rows={3}
            required
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="facilitation-prompt">
            Facilitation guidance for Claude
          </label>
          <span className="field-hint">Optional. How Claude should hold this conversation.</span>
          <textarea
            id="facilitation-prompt"
            value={facilitationPrompt}
            onChange={(e) => setFacilitationPrompt(e.target.value)}
            placeholder="Keep it grounded in concrete stories, not abstractions."
            rows={2}
          />
        </div>
        {error ? (
          <p className="notice notice--error" role="alert">
            Could not create the room. Please try again.
          </p>
        ) : null}
        <div className="btn-row">
          <button className="btn btn--primary" type="submit" disabled={submitting}>
            {submitting ? "Creating" : "Create room"}
          </button>
        </div>
      </form>
    </main>
  );
}
