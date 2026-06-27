"use client";

import { useEffect, useState } from "react";

export function ManageClient(props: { roomId: string; nodeTitle: string }) {
  const { roomId } = props;
  const [key, setKey] = useState("");
  const [harvest, setHarvest] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [finalized, setFinalized] = useState(false);

  useEffect(() => {
    const k = new URLSearchParams(window.location.search).get("key") ?? "";
    setKey(k);
    void fetch(`/api/rooms/${roomId}/harvest?key=${k}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.harvest) {
          setHarvest(d.harvest.body);
          setFinalized(Boolean(d.harvest.finalizedAt));
        }
      });
  }, [roomId]);

  async function weaveNow() {
    setBusy("weave");
    try {
      await fetch(`/api/rooms/${roomId}/weave?key=${key}`, { method: "POST" });
    } finally {
      setBusy(null);
    }
  }

  async function generateHarvest() {
    setBusy("harvest");
    try {
      const res = await fetch(`/api/rooms/${roomId}/harvest?key=${key}`, { method: "POST" });
      if (res.ok) {
        const d = await res.json();
        setHarvest(d.harvest.body);
        setFinalized(false);
      }
    } finally {
      setBusy(null);
    }
  }

  async function saveHarvest(finalize: boolean) {
    setBusy("save");
    try {
      const res = await fetch(`/api/rooms/${roomId}/harvest?key=${key}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body: harvest, finalize }),
      });
      if (res.ok) setFinalized(finalize);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <h1>Manage: {props.nodeTitle}</h1>

      <section>
        <button onClick={weaveNow} disabled={busy !== null}>
          {busy === "weave" ? "Weaving" : "Weave now"}
        </button>
      </section>

      <section>
        <h2>Harvest</h2>
        <button onClick={generateHarvest} disabled={busy !== null}>
          {busy === "harvest" ? "Generating" : "Generate draft"}
        </button>
        <textarea
          value={harvest}
          onChange={(e) => setHarvest(e.target.value)}
          rows={12}
          style={{ width: "100%" }}
        />
        <div>
          <button onClick={() => saveHarvest(false)} disabled={busy !== null || !harvest}>
            Save draft
          </button>
          <button onClick={() => saveHarvest(true)} disabled={busy !== null || !harvest}>
            Finalize
          </button>
          {finalized ? <span> (finalized)</span> : null}
        </div>
      </section>

      <section>
        <h2>Export</h2>
        <a href={`/api/rooms/${roomId}/export?key=${key}`}>Download Kumu CSV</a>
      </section>
    </main>
  );
}
