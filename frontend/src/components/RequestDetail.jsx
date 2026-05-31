import { useEffect, useState } from "react";
import { api } from "../api.js";

function Bar({ value, threshold }) {
  const v = value || 0;
  const tone = v >= threshold ? "good" : v >= 50 ? "mid" : "low";
  return (
    <div className="bar-wrap">
      <div className={`bar ${tone}`} style={{ width: `${v}%` }} />
      <span className="bar-label">{v}</span>
      <span className="bar-threshold" style={{ left: `${threshold}%` }} title={`threshold ${threshold}`} />
    </div>
  );
}

export default function RequestDetail({ requestId, threshold, statuses, onClose, onChanged }) {
  const [req, setReq] = useState(null);
  const [answer, setAnswer] = useState("");
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setReq(await api.getRequest(requestId));
  }
  useEffect(() => { load(); }, [requestId]);

  async function sendAnswer(e) {
    e.preventDefault();
    if (!answer.trim()) return;
    setBusy(true); setError("");
    try {
      await api.refine(requestId, answer);
      setAnswer("");
      await load();
      onChanged?.();
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  async function changeStatus(status) {
    setError("");
    try {
      await api.setStatus(requestId, status);
      await load();
      onChanged?.();
    } catch (e) { setError(e.message); }
  }

  async function sendComment(isPushback) {
    if (!comment.trim()) return;
    setError("");
    try {
      await api.addComment(requestId, { author: "Faktor", body: comment, is_pushback: isPushback });
      setComment("");
      await load();
      onChanged?.();
    } catch (e) { setError(e.message); }
  }

  if (!req) return null;
  const atThreshold = (req.readiness_score || 0) >= threshold;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="detail" onClick={(e) => e.stopPropagation()}>
        <div className="detail-head">
          <h2>{req.title}</h2>
          <button className="close" onClick={onClose}>×</button>
        </div>

        <div className="metrics">
          <div>
            <div className="metric-label">Readiness</div>
            <Bar value={req.readiness_score} threshold={threshold} />
          </div>
          <div>
            <div className="metric-label">Priority</div>
            <Bar value={req.priority_score} threshold={threshold} />
          </div>
        </div>

        <div className="status-row">
          <span>Status:</span>
          <select value={req.status} onChange={(e) => changeStatus(e.target.value)}>
            {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          {!atThreshold && <span className="gate-note">🔒 Ready locked until readiness ≥ {threshold}</span>}
        </div>

        {error && <div className="error">{error}</div>}

        <div className="columns">
          <section className="refine">
            <h3>Refine chat</h3>
            <div className="chat">
              {req.messages.map((m) => (
                <div key={m.id} className={`msg ${m.role}`}>
                  <span className="msg-who">{m.role === "user" ? "You" : "Forge"}</span>
                  <div className="msg-body">{m.content}</div>
                </div>
              ))}
            </div>
            <form onSubmit={sendAnswer} className="chat-input">
              <textarea
                rows={2}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Answer the question to raise readiness…"
              />
              <button type="submit" className="primary" disabled={busy}>
                {busy ? "…" : "Send"}
              </button>
            </form>
          </section>

          <section className="prompt">
            <h3>Dev prompt</h3>
            {req.dev_prompt ? (
              <pre className="dev-prompt">{req.dev_prompt}</pre>
            ) : (
              <div className="empty-prompt">
                Written automatically once readiness clears {threshold}.
              </div>
            )}

            <h3>Comments</h3>
            <div className="comments">
              {req.comments.map((c) => (
                <div key={c.id} className={`comment ${c.is_pushback ? "pushback" : ""}`}>
                  <span className="comment-author">{c.author}{c.is_pushback ? " · pushback" : ""}</span>
                  <div>{c.body}</div>
                </div>
              ))}
              {req.comments.length === 0 && <div className="empty">No comments yet.</div>}
            </div>
            <textarea
              rows={2}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Developer comment or pushback…"
            />
            <div className="comment-actions">
              <button onClick={() => sendComment(false)}>Comment</button>
              <button className="warn" onClick={() => sendComment(true)}>Push back → Refining</button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
