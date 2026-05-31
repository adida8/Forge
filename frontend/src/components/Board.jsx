const LABELS = {
  refining: "Refining",
  ready: "Ready",
  in_review: "In review",
  building: "Building",
  done: "Done",
};

function Score({ label, value }) {
  if (value === null || value === undefined) return null;
  const tone = value >= 80 ? "good" : value >= 50 ? "mid" : "low";
  return (
    <span className={`score ${tone}`}>
      {label} {value}
    </span>
  );
}

export default function Board({ requests, statuses, onSelect }) {
  const cols = statuses.length ? statuses : ["refining", "ready", "in_review", "building", "done"];
  return (
    <div className="board">
      {cols.map((status) => {
        const cards = requests.filter((r) => r.status === status);
        return (
          <div className="column" key={status}>
            <div className="column-head">
              <span>{LABELS[status] || status}</span>
              <span className="count">{cards.length}</span>
            </div>
            <div className="column-body">
              {cards.map((r) => (
                <button className="card" key={r.id} onClick={() => onSelect(r.id)}>
                  <div className="card-title">{r.title}</div>
                  <div className="card-scores">
                    <Score label="P" value={r.priority_score} />
                    <Score label="R" value={r.readiness_score} />
                  </div>
                </button>
              ))}
              {cards.length === 0 && <div className="empty">—</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
