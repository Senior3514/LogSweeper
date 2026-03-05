import React from "react";
import type { LogEvent } from "../api";

interface Props {
  event: LogEvent;
  onBack: () => void;
}

export function EventDetail({ event, onBack }: Props) {
  const containerStyle: React.CSSProperties = { background: "#fff", borderRadius: "8px", padding: "24px", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" };
  const labelStyle: React.CSSProperties = { fontWeight: 600, color: "#666", fontSize: "12px", textTransform: "uppercase", marginBottom: "4px" };
  const valueStyle: React.CSSProperties = { marginBottom: "16px", fontSize: "14px" };

  return (
    <div>
      <button
        onClick={onBack}
        style={{ background: "none", border: "1px solid #ddd", borderRadius: "4px", padding: "6px 12px", cursor: "pointer", marginBottom: "16px", fontSize: "14px" }}
      >
        Back to Events
      </button>
      <div style={containerStyle}>
        <h2 style={{ margin: "0 0 20px", fontSize: "18px" }}>Event #{event.id}</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <div>
            <div style={labelStyle}>Timestamp</div>
            <div style={valueStyle}>{event.timestamp}</div>
          </div>
          <div>
            <div style={labelStyle}>Source</div>
            <div style={valueStyle}>{event.source}</div>
          </div>
          <div>
            <div style={labelStyle}>Hostname</div>
            <div style={valueStyle}>{event.hostname}</div>
          </div>
          <div>
            <div style={labelStyle}>Category</div>
            <div style={valueStyle}>
              <span style={{ background: "#e3f2fd", padding: "2px 8px", borderRadius: "4px" }}>{event.category}</span>
            </div>
          </div>
        </div>
        <div>
          <div style={labelStyle}>Message</div>
          <div style={valueStyle}>{event.message}</div>
        </div>
        <div>
          <div style={labelStyle}>Raw</div>
          <pre style={{ background: "#f5f5f5", padding: "12px", borderRadius: "4px", overflow: "auto", fontSize: "12px", fontFamily: "monospace" }}>
            {event.raw}
          </pre>
        </div>
      </div>
    </div>
  );
}
