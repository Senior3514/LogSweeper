import React from "react";
import type { LogEvent } from "../api";

interface Props {
  event: LogEvent;
  onBack: () => void;
}

export function EventDetail({ event, onBack }: Props) {
  const containerStyle: React.CSSProperties = {
    background: "#fff",
    borderRadius: "8px",
    padding: "24px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  };

  const labelStyle: React.CSSProperties = {
    fontWeight: 600,
    color: "#6b7280",
    fontSize: "11px",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    marginBottom: "4px",
  };

  const valueStyle: React.CSSProperties = {
    marginBottom: "16px",
    fontSize: "14px",
    color: "#111827",
  };

  const categoryColors: Record<string, string> = {
    json: "#dbeafe",
    raw: "#fef3c7",
    syslog: "#d1fae5",
    error: "#fee2e2",
  };

  return (
    <div>
      <button
        onClick={onBack}
        style={{
          background: "none",
          border: "1px solid #d1d5db",
          borderRadius: "6px",
          padding: "6px 14px",
          cursor: "pointer",
          marginBottom: "16px",
          fontSize: "14px",
          color: "#374151",
          transition: "background 0.15s",
        }}
        onMouseOver={e => (e.currentTarget.style.background = "#f3f4f6")}
        onMouseOut={e => (e.currentTarget.style.background = "none")}
      >
        Back to Events
      </button>
      <div style={containerStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", borderBottom: "1px solid #e5e7eb", paddingBottom: "16px" }}>
          <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 600, color: "#111827" }}>Event #{event.id}</h2>
          <span style={{
            background: categoryColors[event.category] || "#f3f4f6",
            padding: "4px 12px",
            borderRadius: "12px",
            fontSize: "12px",
            fontWeight: 500,
          }}>
            {event.category}
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <div>
            <div style={labelStyle}>Timestamp</div>
            <div style={{ ...valueStyle, fontFamily: "monospace", fontSize: "13px" }}>{event.timestamp}</div>
          </div>
          <div>
            <div style={labelStyle}>Source</div>
            <div style={valueStyle}>{event.source}</div>
          </div>
          <div>
            <div style={labelStyle}>Hostname</div>
            <div style={valueStyle}>{event.hostname || "—"}</div>
          </div>
          <div>
            <div style={labelStyle}>Created At</div>
            <div style={{ ...valueStyle, fontFamily: "monospace", fontSize: "13px" }}>{event.created_at || "—"}</div>
          </div>
        </div>
        <div>
          <div style={labelStyle}>Message</div>
          <div style={{ ...valueStyle, lineHeight: 1.5 }}>{event.message}</div>
        </div>
        <div>
          <div style={labelStyle}>Raw Log</div>
          <pre style={{
            background: "#1a1a2e",
            color: "#e5e7eb",
            padding: "16px",
            borderRadius: "6px",
            overflow: "auto",
            fontSize: "12px",
            fontFamily: "monospace",
            lineHeight: 1.6,
            margin: 0,
          }}>
            {event.raw}
          </pre>
        </div>
      </div>
    </div>
  );
}
