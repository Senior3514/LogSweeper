const BASE = "";

export interface LogEvent {
  id: number;
  timestamp: string;
  source: string;
  hostname: string;
  category: string;
  message: string;
  raw: string;
  created_at: string;
}

export interface EventsResponse {
  events: LogEvent[];
  total: number;
  limit: number;
  offset: number;
}

export async function fetchEvents(params: {
  source?: string;
  category?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<EventsResponse> {
  const qs = new URLSearchParams();
  if (params.source) qs.set("source", params.source);
  if (params.category) qs.set("category", params.category);
  if (params.search) qs.set("search", params.search);
  if (params.limit) qs.set("limit", String(params.limit));
  if (params.offset) qs.set("offset", String(params.offset));
  const res = await fetch(`${BASE}/api/events?${qs}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchEvent(id: number): Promise<LogEvent> {
  const res = await fetch(`${BASE}/api/events/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchSources(): Promise<string[]> {
  const res = await fetch(`${BASE}/api/sources`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.sources;
}

export async function fetchCategories(): Promise<string[]> {
  const res = await fetch(`${BASE}/api/categories`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.categories;
}

export async function checkHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${BASE}/healthz`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
