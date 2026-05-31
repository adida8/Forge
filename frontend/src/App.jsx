import { useEffect, useState } from "react";
import { api } from "./api.js";
import Board from "./components/Board.jsx";
import IntakeForm from "./components/IntakeForm.jsx";
import RequestDetail from "./components/RequestDetail.jsx";

export default function App() {
  const [config, setConfig] = useState({ readiness_threshold: 80, statuses: [], engine: "fallback" });
  const [requests, setRequests] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [intakeOpen, setIntakeOpen] = useState(false);

  async function refresh() {
    setRequests(await api.listRequests());
  }

  useEffect(() => {
    api.config().then(setConfig);
    refresh();
  }, []);

  async function handleCreate(body) {
    const created = await api.createRequest(body);
    setIntakeOpen(false);
    await refresh();
    setSelectedId(created.id);
  }

  const selected = requests.find((r) => r.id === selectedId);

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>The Forge</h1>
          <p className="tagline">Specs aren't ready until they're buildable.</p>
        </div>
        <div className="topbar-right">
          <span className={`engine-pill ${config.engine}`}>
            engine: {config.engine}
          </span>
          <button className="primary" onClick={() => setIntakeOpen(true)}>
            + New request
          </button>
        </div>
      </header>

      <Board
        requests={requests}
        statuses={config.statuses}
        onSelect={setSelectedId}
      />

      {intakeOpen && (
        <IntakeForm onCreate={handleCreate} onClose={() => setIntakeOpen(false)} />
      )}

      {selected && (
        <RequestDetail
          requestId={selected.id}
          threshold={config.readiness_threshold}
          statuses={config.statuses}
          onClose={() => setSelectedId(null)}
          onChanged={refresh}
        />
      )}
    </div>
  );
}
