import React, { useEffect, useState, useCallback } from "react";
import { fetchEvents, fetchSources, fetchCategories, fetchStats } from "../api";
import type { LogEvent, EventsResponse, StatsResponse } from "../api";

interface Props {
  onSelectEvent: (event: LogEvent) => void;
}

const PAGE_SIZE = 50;

export function Dashboard({ onSelectEvent }: Props) {
  const [data, setData] = useState<EventsResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [source, setSource] = useState("");
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(false);

  const load = useCallback(async (currentPage = page) => {
    setLoading(true);
    setError("");
    try {
      const result = await fetchEvents({
        source: source || undefined,
        category: category || undefined,
        search: search || undefined,
        limit: PAGE_SIZE,
        offset: currentPage * PAGE_SIZE,
      });
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load events");
    }
    setLoading(false);
  }, [source, category, search, page]);

  const loadMeta = useCallback(async () => {
    try {
      const [s, c, st] = await Promise.all([fetchSources(), fetchCategories(), fetchStats()]);
      setSources(s);
      setCategories(c);
      setStats(st);
    } catch {
      // Stats are non-critical
    }
  }, []);

  useEffect(() => {
    load(page);
  }, [page]);

  useEffect(() => {
    load(0);
    setPage(0);
    loadMeta();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      load(page);
      loadMeta();
    }, 10_000);
    return () => clearInterval(interval);
  }, [autoRefresh, page, load, loadMeta]);

  const handleSearch = () => {
    setPage(0);
    load(0);
    loadMeta();
  };

  const handleReset = () => {
    setSource("");
    setCategory("");
    setSearch("");
    setPage(0);
  };

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  const cardStyle: React.CSSProperties = {
    background: "#fff",
    borderRadius: "8px",
    padding: "16px 20px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    textAlign: "center",
  };

  const containerStyle: React.CSSProperties = {
    background: "#fff",
    borderRadius: "8px",
    padding: "20px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  };

  const inputStyle: React.CSSProperties = {
    padding: "8px 12px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
    fontSize: "14px",
    outline: "none",
    transition: "border-color 0.15s",
  };

  const btnPrimary: React.CSSProperties = {
    padding: "8px 20px",
    background: "#1a1a2e",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: 500,
    transition: "background 0.15s",
  };

  const btnSecondary: React.CSSProperties = {
    ...btnPrimary,
    background: "#6b7280",
  };

  const categoryColors: Record<string, string> = {
    json: "#dbeafe",
    raw: "#fef3c7",
    syslog: "#d1fae5",
    error: "#fee2e2",
  };

  return (
    <div>
      {/* Stats cards */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", marginBottom: "16px" }}>
          <div style={cardStyle}>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "#1a1a2e" }}>{stats.total_events.toLocaleString()}</div>
            <div style={{ fontSize: "12px", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginTop: "4px" }}>Total Events</div>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "#2563eb" }}>{stats.source_count}</div>
            <div style={{ fontSize: "12px", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginTop: "4px" }}>Sources</div>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "#059669" }}>{stats.category_count}</div>
            <div style={{ fontSize: "12px", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginTop: "4px" }}>Categories</div>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: "28px", fontWeight: 700, color: autoRefresh ? "#059669" : "#9ca3af" }}>
              {autoRefresh ? "ON" : "OFF"}
            </div>
            <div
              style={{ fontSize: "12px", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginTop: "4px", cursor: "pointer" }}
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              Live Refresh
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ ...containerStyle, marginBottom: "16px", display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
        <select style={inputStyle} value={source} onChange={e => setSource(e.target.value)}>
          <option value="">All Sources</option>
          {sources.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select style={inputStyle} value={category} onChange={e => setCategory(e.target.value)}>
          <option value="">All Categories</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <input
          style={{ ...inputStyle, flex: 1, minWidth: "200px" }}
          placeholder="Search messages..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSearch()}
        />
        <button style={btnPrimary} onClick={handleSearch}>Search</button>
        <button style={btnSecondary} onClick={handleReset}>Reset</button>
      </div>

      {/* Events table */}
      <div style={containerStyle}>
        {loading && <p style={{ color: "#6b7280" }}>Loading events...</p>}
        {error && <p style={{ color: "#dc2626", fontWeight: 500 }}>{error}</p>}
        {data && !loading && (
          <>
            <div style={{ marginBottom: "12px", fontSize: "14px", color: "#6b7280", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>{data.total.toLocaleString()} events found</span>
              {totalPages > 1 && (
                <span>Page {page + 1} of {totalPages}</span>
              )}
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #e5e7eb", textAlign: "left" }}>
                  <th style={{ padding: "10px 8px", color: "#374151", fontWeight: 600, fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Time</th>
                  <th style={{ padding: "10px 8px", color: "#374151", fontWeight: 600, fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Source</th>
                  <th style={{ padding: "10px 8px", color: "#374151", fontWeight: 600, fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Category</th>
                  <th style={{ padding: "10px 8px", color: "#374151", fontWeight: 600, fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Message</th>
                </tr>
              </thead>
              <tbody>
                {data.events.map(event => (
                  <tr
                    key={event.id}
                    onClick={() => onSelectEvent(event)}
                    style={{ borderBottom: "1px solid #f3f4f6", cursor: "pointer", transition: "background 0.1s" }}
                    onMouseOver={e => (e.currentTarget.style.background = "#f9fafb")}
                    onMouseOut={e => (e.currentTarget.style.background = "")}
                  >
                    <td style={{ padding: "10px 8px", whiteSpace: "nowrap", fontFamily: "monospace", fontSize: "12px", color: "#4b5563" }}>
                      {event.timestamp}
                    </td>
                    <td style={{ padding: "10px 8px", fontWeight: 500 }}>{event.source}</td>
                    <td style={{ padding: "10px 8px" }}>
                      <span style={{
                        background: categoryColors[event.category] || "#f3f4f6",
                        padding: "2px 10px",
                        borderRadius: "12px",
                        fontSize: "12px",
                        fontWeight: 500,
                      }}>
                        {event.category}
                      </span>
                    </td>
                    <td style={{ padding: "10px 8px", maxWidth: "500px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#4b5563" }}>
                      {event.message}
                    </td>
                  </tr>
                ))}
                {data.events.length === 0 && (
                  <tr>
                    <td colSpan={4} style={{ padding: "40px", textAlign: "center", color: "#9ca3af" }}>
                      No events found. Try adjusting your filters or ingesting some logs.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div style={{ display: "flex", justifyContent: "center", gap: "8px", marginTop: "16px", alignItems: "center" }}>
                <button
                  style={{ ...btnSecondary, opacity: page === 0 ? 0.5 : 1 }}
                  disabled={page === 0}
                  onClick={() => setPage(0)}
                >
                  First
                </button>
                <button
                  style={{ ...btnSecondary, opacity: page === 0 ? 0.5 : 1 }}
                  disabled={page === 0}
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                >
                  Prev
                </button>
                <span style={{ padding: "8px 16px", fontSize: "14px", color: "#374151", fontWeight: 500 }}>
                  {page + 1} / {totalPages}
                </span>
                <button
                  style={{ ...btnSecondary, opacity: page >= totalPages - 1 ? 0.5 : 1 }}
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next
                </button>
                <button
                  style={{ ...btnSecondary, opacity: page >= totalPages - 1 ? 0.5 : 1 }}
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage(totalPages - 1)}
                >
                  Last
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
