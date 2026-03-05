import React, { useEffect, useState } from "react";
import { fetchEvents, fetchSources, fetchCategories } from "../api";
import type { LogEvent, EventsResponse } from "../api";

interface Props {
  onSelectEvent: (event: LogEvent) => void;
}

export function Dashboard({ onSelectEvent }: Props) {
  const [data, setData] = useState<EventsResponse | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [source, setSource] = useState("");
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await fetchEvents({ source: source || undefined, category: category || undefined, search: search || undefined });
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load events");
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
    fetchSources().then(setSources).catch(() => {});
    fetchCategories().then(setCategories).catch(() => {});
  }, []);

  const containerStyle: React.CSSProperties = { background: "#fff", borderRadius: "8px", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" };
  const inputStyle: React.CSSProperties = { padding: "8px 12px", border: "1px solid #ddd", borderRadius: "4px", fontSize: "14px" };
  const btnStyle: React.CSSProperties = { padding: "8px 16px", background: "#1a1a2e", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "14px" };

  return (
    <div>
      <div style={{ ...containerStyle, marginBottom: "16px", display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
        <select style={inputStyle} value={source} onChange={e => setSource(e.target.value)}>
          <option value="">All Sources</option>
          {sources.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select style={inputStyle} value={category} onChange={e => setCategory(e.target.value)}>
          <option value="">All Categories</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <input style={{ ...inputStyle, flex: 1, minWidth: "200px" }} placeholder="Search messages..." value={search} onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === "Enter" && load()} />
        <button style={btnStyle} onClick={load}>Search</button>
      </div>

      <div style={containerStyle}>
        {loading && <p>Loading...</p>}
        {error && <p style={{ color: "red" }}>{error}</p>}
        {data && !loading && (
          <>
            <div style={{ marginBottom: "12px", fontSize: "14px", color: "#666" }}>
              {data.total} events found
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #eee", textAlign: "left" }}>
                  <th style={{ padding: "8px" }}>Time</th>
                  <th style={{ padding: "8px" }}>Source</th>
                  <th style={{ padding: "8px" }}>Category</th>
                  <th style={{ padding: "8px" }}>Message</th>
                </tr>
              </thead>
              <tbody>
                {data.events.map(event => (
                  <tr key={event.id} onClick={() => onSelectEvent(event)} style={{ borderBottom: "1px solid #f0f0f0", cursor: "pointer" }} onMouseOver={e => (e.currentTarget.style.background = "#f8f9fa")} onMouseOut={e => (e.currentTarget.style.background = "")}>
                    <td style={{ padding: "8px", whiteSpace: "nowrap", fontFamily: "monospace", fontSize: "12px" }}>{event.timestamp}</td>
                    <td style={{ padding: "8px" }}>{event.source}</td>
                    <td style={{ padding: "8px" }}>
                      <span style={{ background: "#e3f2fd", padding: "2px 8px", borderRadius: "4px", fontSize: "12px" }}>{event.category}</span>
                    </td>
                    <td style={{ padding: "8px", maxWidth: "500px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{event.message}</td>
                  </tr>
                ))}
                {data.events.length === 0 && (
                  <tr><td colSpan={4} style={{ padding: "24px", textAlign: "center", color: "#999" }}>No events found</td></tr>
                )}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
}
