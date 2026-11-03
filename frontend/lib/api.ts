export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const ACCEPTED_TYPES = [".pdf", ".pptx", ".docx", ".txt", ".md"];

export type DocStatus = "processing" | "ready" | "failed";

export interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string;
  status: DocStatus;
  chunk_count: number;
  error: string | null;
  created_at: string;
}

export interface Source {
  n: number;
  doc_id: string;
  filename: string;
  page: number | null;
  slide: number | null;
  score: number;
  text: string;
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface Health {
  ok: boolean;
  pinecone_configured: boolean;
  llm_configured: boolean;
  llm_model: string;
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
  } catch {
    return `${res.status} ${res.statusText}`;
  }
}

export async function getHealth(): Promise<Health> {
  const res = await fetch(`${API_URL}/api/health`);
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json();
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_URL}/api/documents`);
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json();
}

export async function uploadDocuments(files: File[]): Promise<DocumentInfo[]> {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  const res = await fetch(`${API_URL}/api/documents`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/documents/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await errorMessage(res));
}

export interface ChatHandlers {
  onSources: (sources: Source[]) => void;
  onToken: (token: string) => void;
}

/** POST a question and consume the server-sent event stream until `done` or `error`. */
export async function streamChat(
  body: { question: string; history: ChatTurn[]; doc_ids: string[] | null },
  handlers: ChatHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(await errorMessage(res));

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

    let boundary;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      let event = "message";
      let data = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      const payload = data ? JSON.parse(data) : null;

      if (event === "sources") handlers.onSources(payload);
      else if (event === "token") handlers.onToken(payload);
      else if (event === "error") throw new Error(payload?.message ?? "Chat failed");
      else if (event === "done") return;
    }
  }
}
