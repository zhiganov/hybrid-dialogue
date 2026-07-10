"use client";

import { useEffect, useRef, useState } from "react";
import { ROOM_FIELD_LIMITS } from "@/lib/domain";

export function ManageClient(props: {
  roomId: string;
  nodeTitle: string;
  nodeDescription: string;
  facilitationPrompt: string;
  listed: boolean;
}) {
  const { roomId } = props;
  const [key, setKey] = useState("");
  const [title, setTitle] = useState(props.nodeTitle);
  const [description, setDescription] = useState(props.nodeDescription);
  const [prompt, setPrompt] = useState(props.facilitationPrompt);
  const [saved, setSaved] = useState({
    title: props.nodeTitle,
    description: props.nodeDescription,
    prompt: props.facilitationPrompt,
  });
  const [savedNote, setSavedNote] = useState(false);
  const [harvest, setHarvest] = useState("");
  const [hasHarvest, setHasHarvest] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [listed, setListed] = useState(props.listed);
  const [finalized, setFinalized] = useState(false);
  const [weaveNote, setWeaveNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmFinalize, setConfirmFinalize] = useState(false);
  const confirmTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (confirmTimer.current) clearTimeout(confirmTimer.current);
    };
  }, []);

  function onFinalizeClick() {
    if (!confirmFinalize) {
      setConfirmFinalize(true);
      if (confirmTimer.current) clearTimeout(confirmTimer.current);
      confirmTimer.current = setTimeout(() => setConfirmFinalize(false), 5000);
      return;
    }
    if (confirmTimer.current) clearTimeout(confirmTimer.current);
    setConfirmFinalize(false);
    void saveHarvest(true);
  }

  useEffect(() => {
    const k = new URLSearchParams(window.location.search).get("key") ?? "";
    setKey(k);
    void fetch(`/api/rooms/${roomId}/harvest?key=${k}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.harvest) {
          setHarvest(d.harvest.body);
          setHasHarvest(true);
          setFinalized(Boolean(d.harvest.finalizedAt));
        }
      })
      .catch(() => {});
  }, [roomId]);

  async function weaveNow() {
    setBusy("weave");
    setError(null);
    setWeaveNote(null);
    try {
      const res = await fetch(`/api/rooms/${roomId}/weave?key=${key}`, { method: "POST" });
      if (!res.ok) {
        const d = await res.json().catch(() => null);
        setError(d?.message ?? "The weave did not post. Please try again.");
        return;
      }
      setWeaveNote("A weave was posted to the room.");
    } catch {
      setError("The weave did not post. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  async function toggleListed() {
    setBusy("listed");
    setError(null);
    const next = !listed;
    try {
      const res = await fetch(`/api/rooms/${roomId}?key=${key}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ listed: next }),
      });
      if (!res.ok) {
        setError("Could not update lobby visibility. Please try again.");
        return;
      }
      setListed(next);
    } catch {
      setError("Could not update lobby visibility. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  async function generateHarvest() {
    setBusy("harvest");
    setError(null);
    try {
      const res = await fetch(`/api/rooms/${roomId}/harvest?key=${key}`, { method: "POST" });
      if (!res.ok) {
        const d = await res.json().catch(() => null);
        setError(d?.message ?? "Could not generate a draft. Please try again.");
        return;
      }
      const d = await res.json();
      setHarvest(d.harvest.body);
      setHasHarvest(true);
      setFinalized(false);
    } catch {
      setError("Could not generate a draft. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  async function saveHarvest(finalize: boolean) {
    setBusy("save");
    setError(null);
    try {
      const res = await fetch(`/api/rooms/${roomId}/harvest?key=${key}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body: harvest, finalize }),
      });
      if (!res.ok) {
        setError("Could not save the harvest. Please try again.");
        return;
      }
      setHasHarvest(true);
      setFinalized(finalize);
    } catch {
      setError("Could not save the harvest. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  async function saveEdits() {
    setBusy("edit");
    setError(null);
    setSavedNote(false);
    const next = {
      nodeTitle: title.trim(),
      nodeDescription: description.trim(),
      facilitationPrompt: prompt.trim(),
    };
    try {
      const res = await fetch(`/api/rooms/${roomId}?key=${key}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(next),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => null);
        setError(d?.message ?? "Could not save changes. Please try again.");
        return;
      }
      setTitle(next.nodeTitle);
      setDescription(next.nodeDescription);
      setPrompt(next.facilitationPrompt);
      setSaved({
        title: next.nodeTitle,
        description: next.nodeDescription,
        prompt: next.facilitationPrompt,
      });
      setSavedNote(true);
    } catch {
      setError("Could not save changes. Please try again.");
    } finally {
      setBusy(null);
    }
  }

  const editsDirty =
    title.trim() !== saved.title ||
    description.trim() !== saved.description ||
    prompt.trim() !== saved.prompt;
  const editsValid = Boolean(title.trim() && description.trim() && prompt.trim());

  return (
    <main className="page">
      <header className="page-head">
        <p className="status">Conversation designer view</p>
        <h1 className="title">{title}</h1>
        <p className="field-hint">
          You convene this conversation. Weave while it is live to connect what people
          say; harvest and export it when it is done.
        </p>
      </header>

      {error ? (
        <p className="notice notice--error" role="alert">
          {error}
        </p>
      ) : null}

      <section className="panel">
        <h2 className="section-title">Edit conversation</h2>
        <p className="field-hint">
          Change how this conversation reads and how Claude facilitates it. Edits show up
          in the lobby and the room; they do not rewrite past messages or the harvest.
        </p>
        <div className="field">
          <label className="field-label" htmlFor="edit-title">
            Title
          </label>
          <input
            id="edit-title"
            value={title}
            maxLength={ROOM_FIELD_LIMITS.nodeTitle}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="edit-description">
            Description
          </label>
          <textarea
            id="edit-description"
            value={description}
            rows={3}
            maxLength={ROOM_FIELD_LIMITS.nodeDescription}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="edit-prompt">
            How Claude facilitates
          </label>
          <textarea
            id="edit-prompt"
            value={prompt}
            rows={5}
            maxLength={ROOM_FIELD_LIMITS.facilitationPrompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <p className="field-hint">
            Advanced. Shapes Claude&apos;s stance in this room; it takes effect on the
            next weave or reply.
          </p>
        </div>
        <div className="btn-row">
          <button
            className="btn btn--quiet"
            onClick={saveEdits}
            disabled={busy !== null || !editsDirty || !editsValid}
          >
            {busy === "edit" ? "Saving" : "Save changes"}
          </button>
          {savedNote && !editsDirty ? (
            <span className="status status--done">&#10003; Saved</span>
          ) : null}
        </div>
      </section>

      <section className="panel">
        <h2 className="section-title">Lobby</h2>
        <p className="field-hint">
          {listed
            ? "Listed on the home page so people can find and join this conversation."
            : "Hidden from the home page. Only people with the link can join."}
        </p>
        <div className="btn-row">
          <button className="btn btn--quiet" onClick={toggleListed} disabled={busy !== null}>
            {busy === "listed" ? "Updating" : listed ? "Hide from lobby" : "Show in lobby"}
          </button>
        </div>
      </section>

      <section className="panel">
        <h2 className="section-title">Weave</h2>
        <p className="field-hint">
          Ask Claude to post one weave now, connecting what people have said.
          Claude also weaves on its own as the conversation grows.
        </p>
        <div className="btn-row">
          <button className="btn btn--quiet" onClick={weaveNow} disabled={busy !== null}>
            {busy === "weave" ? "Weaving" : "Weave now"}
          </button>
          {weaveNote ? <span className="status status--done">&#10003; {weaveNote}</span> : null}
        </div>
      </section>

      <section className="panel">
        <h2 className="section-title">Harvest</h2>
        <p className="field-hint">
          Distill the conversation into a draft, edit it freely, then finalize.
        </p>
        <div className="btn-row">
          <button className="btn btn--quiet" onClick={generateHarvest} disabled={busy !== null}>
            {busy === "harvest" ? "Generating" : hasHarvest ? "Regenerate draft" : "Generate draft"}
          </button>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="harvest">
            Harvest
          </label>
          <textarea
            id="harvest"
            value={harvest}
            onChange={(e) => setHarvest(e.target.value)}
            rows={14}
            placeholder="Generate a draft to begin, or write the harvest yourself."
          />
        </div>
        <div className="btn-row">
          <button
            className="btn btn--quiet"
            onClick={() => saveHarvest(false)}
            disabled={busy !== null || !harvest.trim()}
          >
            Save draft
          </button>
          <button
            className="btn btn--primary"
            onClick={onFinalizeClick}
            disabled={busy !== null || !harvest.trim()}
          >
            {confirmFinalize ? "Tap again to finalize" : "Finalize"}
          </button>
          {finalized ? <span className="status status--done">&#10003; Finalized</span> : null}
        </div>
      </section>

      <section className="panel">
        <h2 className="section-title">Export</h2>
        {hasHarvest ? (
          <p>
            <a className="link" href={`/api/rooms/${roomId}/export?key=${key}`}>
              Download Kumu CSV
            </a>
          </p>
        ) : (
          <p className="field-hint">
            Export becomes available once you generate or save a harvest.
          </p>
        )}
      </section>
    </main>
  );
}
