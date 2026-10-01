import { getAccessToken } from "./auth";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type DocumentRecord = {
  id: string;
  filename: string;
  content_type: string;
  status: string;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const response = await fetch(`${apiUrl}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token ?? ""}`,
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function listDocuments(): Promise<DocumentRecord[]> {
  return request<DocumentRecord[]>("/api/v1/documents");
}

export function uploadDocument(file: File): Promise<DocumentRecord> {
  const formData = new FormData();
  formData.append("file", file);
  return request<DocumentRecord>("/api/v1/documents", { method: "POST", body: formData });
}

export function retryDocument(documentId: string): Promise<DocumentRecord> {
  return request<DocumentRecord>(`/api/v1/documents/${documentId}/retry`, { method: "POST" });
}
