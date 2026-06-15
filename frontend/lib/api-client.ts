export interface Voice {
  name: string;
  description: string;
}

export interface VoicesResponse {
  voices: Voice[];
}

export type InputSource = "text" | "md";

export interface SynthesizeRequest {
  text: string;
  voice: string;
  style?: string;
  pacing?: string;
  accent?: string;
  source?: InputSource;
}

export interface SynthesizeMetadata {
  text_excerpt: string;
  char_count: number;
  source: string;
  voice: string;
  pacing: string;
  style: string;
  accent: string;
}

export interface SynthesizeSuccessResponse {
  id: string;
  created_at: string;
  metadata: SynthesizeMetadata;
  audio_url: string;
}

export interface SynthesizeErrorResponse {
  id: string;
  detail: string;
}

export async function fetchVoices(): Promise<VoicesResponse> {
  const res = await fetch("/api/voices");
  if (!res.ok) {
    throw new Error(`Failed to fetch voices: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function synthesizeSpeech(
  request: SynthesizeRequest,
): Promise<SynthesizeSuccessResponse> {
  const res = await fetch("/api/synthesize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    let detail = `Synthesis failed: ${res.status} ${res.statusText}`;
    try {
      const errBody: SynthesizeErrorResponse = await res.json();
      detail = errBody.detail || detail;
    } catch {
      /* ignore parse errors, use fallback detail */
    }
    throw new Error(detail);
  }

  return res.json();
}

export function audioDownloadUrl(audioUrl: string): string {
  return `${audioUrl}?download=true`;
}

export interface HistoryItem {
  id: string;
  created_at: string;
  text_excerpt: string;
  char_count: number;
  source: string;
  voice: string;
  pacing: string | null;
  style: string | null;
  accent: string | null;
  format: string;
  duration_ms: number | null;
  status: string;
  audio_url: string;
}

export interface HistoryListResponse {
  items: HistoryItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export async function fetchHistory(
  limit: number = 50,
  offset: number = 0,
): Promise<HistoryListResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const res = await fetch(`/api/history?${params}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch history: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function deleteHistoryItem(id: string): Promise<void> {
  const res = await fetch(`/api/history/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(`Failed to delete history item: ${res.status} ${res.statusText}`);
  }
}
