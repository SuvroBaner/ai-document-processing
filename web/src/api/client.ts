const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// Dev-token shortcut for the slice (frontend auth deferred — see PROPOSAL.md §4).
const DEV_TOKEN = "dev-token";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${DEV_TOKEN}`,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  queue: () => request<QueueItem[]>("/review/queue"),
  review: (id: string) => request<ReviewPayload>(`/review/${id}`),
  patchField: (docId: string, fieldId: string, body: { new_value: unknown; reason?: string }) =>
    request<{ id: string }>(`/review/${docId}/fields/${fieldId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  approve: (docId: string, reason?: string) =>
    request<{ id: string; current_state: string }>(`/review/${docId}/approve`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
};

export type QueueItem = {
  id: string;
  filename: string;
  kind: string;
  state: string;
};

export type Citation = {
  page: number;
  bbox: [number, number, number, number];
  source_text: string;
};

export type Field = {
  id: string;
  field_path: string;
  value: unknown;
  confidence: number;
  citations: Citation[];
};

export type ReviewPayload = {
  document: { id: string; filename: string; state: string; pdf_url: string };
  extraction: { id: string; schema_id: string; fields: Field[] } | null;
};
