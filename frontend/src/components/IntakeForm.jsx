import { useState } from "react";

export default function IntakeForm({ onCreate, onClose }) {
  const [title, setTitle] = useState("");
  const [rawIdea, setRawIdea] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    if (!title.trim() || !rawIdea.trim()) return;
    setBusy(true);
    setError("");
    try {
      await onCreate({ title, raw_idea: rawIdea, created_by: "Adi" });
    } catch (err) {
      setError(err.message || "Could not start refining. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>New request</h2>
        <form onSubmit={submit}>
          <label>Title</label>
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="One-line name for the idea"
          />
          <label>Rough idea</label>
          <textarea
            rows={4}
            value={rawIdea}
            onChange={(e) => setRawIdea(e.target.value)}
            placeholder="Drop the rough idea. The Forge will interrogate the gaps."
          />
          {error && <div className="error">{error}</div>}
          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button type="submit" className="primary" disabled={busy}>
              {busy ? "Starting…" : "Start refining"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
