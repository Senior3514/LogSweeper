import React, { useEffect, useState } from "react";
import { Dashboard } from "./components/Dashboard";
import { EventDetail } from "./components/EventDetail";
import type { LogEvent } from "./api";

export function App() {
  const [selectedEvent, setSelectedEvent] = useState<LogEvent | null>(null);

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", margin: 0, padding: 0, background: "#f5f5f5", minHeight: "100vh" }}>
      <header style={{ background: "#1a1a2e", color: "#fff", padding: "12px 24px", display: "flex", alignItems: "center", gap: "12px" }}>
        <h1 style={{ margin: 0, fontSize: "20px", fontWeight: 600 }}>LogSweeper</h1>
        <span style={{ opacity: 0.6, fontSize: "14px" }}>Universal Log Explorer</span>
      </header>
      <main style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
        {selectedEvent ? (
          <EventDetail event={selectedEvent} onBack={() => setSelectedEvent(null)} />
        ) : (
          <Dashboard onSelectEvent={setSelectedEvent} />
        )}
      </main>
    </div>
  );
}
