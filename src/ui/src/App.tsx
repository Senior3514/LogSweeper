import { useEffect, useState } from "react";
import { Dashboard } from "./components/Dashboard";
import { EventDetail } from "./components/EventDetail";
import { checkHealth } from "./api";
import type { LogEvent } from "./api";

export function App() {
  const [selectedEvent, setSelectedEvent] = useState<LogEvent | null>(null);
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [version, setVersion] = useState("");

  useEffect(() => {
    checkHealth()
      .then(data => {
        setHealthy(true);
        setVersion(data.version);
      })
      .catch(() => setHealthy(false));
  }, []);

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, sans-serif", margin: 0, padding: 0, background: "#f3f4f6", minHeight: "100vh" }}>
      <header style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        color: "#fff",
        padding: "0 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: "56px",
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <h1 style={{ margin: 0, fontSize: "20px", fontWeight: 700, letterSpacing: "-0.02em" }}>LogSweeper</h1>
          <span style={{ opacity: 0.5, fontSize: "13px", fontWeight: 400 }}>Universal Log Explorer</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "13px" }}>
          {version && <span style={{ opacity: 0.5 }}>v{version}</span>}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <div style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: healthy === true ? "#34d399" : healthy === false ? "#f87171" : "#9ca3af",
            }} />
            <span style={{ opacity: 0.7 }}>{healthy === true ? "Connected" : healthy === false ? "Disconnected" : "..."}</span>
          </div>
        </div>
      </header>
      <main style={{ padding: "24px", maxWidth: "1400px", margin: "0 auto" }}>
        {selectedEvent ? (
          <EventDetail event={selectedEvent} onBack={() => setSelectedEvent(null)} />
        ) : (
          <Dashboard onSelectEvent={setSelectedEvent} />
        )}
      </main>
    </div>
  );
}
