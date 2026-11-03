"use client";

import { useCallback, useEffect, useState } from "react";
import ChatWindow from "@/components/ChatWindow";
import DocumentList from "@/components/DocumentList";
import UploadDropzone from "@/components/UploadDropzone";
import { deleteDocument, getHealth, listDocuments, type DocumentInfo, type Health } from "@/lib/api";

const POLL_MS = 2000;

export default function Home() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [health, setHealth] = useState<Health | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [docs, status] = await Promise.all([listDocuments(), getHealth()]);
      setDocuments(docs);
      setHealth(status);
      setBackendError(null);
    } catch {
      setBackendError("Can't reach the backend. Is FastAPI running on port 8000?");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll while any document is still being indexed, or until the backend comes up.
  const processing = documents.some((d) => d.status === "processing");
  useEffect(() => {
    if (!processing && !backendError) return;
    const timer = setInterval(refresh, POLL_MS);
    return () => clearInterval(timer);
  }, [processing, backendError, refresh]);

  // Drop selections for documents that were deleted.
  useEffect(() => {
    setSelected((prev) => new Set([...prev].filter((id) => documents.some((d) => d.id === id))));
  }, [documents]);

  async function handleDelete(id: string) {
    const doc = documents.find((d) => d.id === id);
    if (!doc || !confirm(`Delete "${doc.filename}"? Its indexed chunks will be removed.`)) return;
    try {
      await deleteDocument(id);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
    refresh();
  }

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const readyCount = documents.filter((d) => d.status === "ready").length;
  const missingKeys = health && (!health.pinecone_configured || !health.llm_configured);

  return (
    <div className="flex h-dvh flex-col md:flex-row">
      <aside className="flex max-h-[45dvh] w-full shrink-0 flex-col border-b border-stone-200 bg-stone-100/70 md:max-h-none md:w-80 md:border-r md:border-b-0 dark:border-stone-800 dark:bg-stone-900/50">
        <div className="px-5 pt-5 pb-4">
          <h1 className="text-lg font-semibold tracking-tight">Noteful</h1>
          <p className="text-xs text-stone-500 dark:text-stone-400">Ask questions about your study material</p>
        </div>
        <div className="px-4">
          <UploadDropzone onUploaded={refresh} />
        </div>
        <div className="mt-5 flex items-center justify-between px-5 pb-2">
          <h2 className="text-xs font-semibold tracking-wide text-stone-500 uppercase dark:text-stone-400">
            Documents
          </h2>
          {selected.size > 0 && (
            <button
              type="button"
              onClick={() => setSelected(new Set())}
              className="text-xs text-indigo-600 hover:underline dark:text-indigo-400"
            >
              Clear selection
            </button>
          )}
        </div>
        <div className="flex-1 overflow-y-auto px-4 pb-4">
          <DocumentList documents={documents} selected={selected} onToggle={toggle} onDelete={handleDelete} />
          {readyCount > 1 && (
            <p className="mt-3 px-1 text-xs text-stone-500 dark:text-stone-400">
              Tick documents to limit the chat to them. Nothing ticked searches everything.
            </p>
          )}
        </div>
      </aside>

      <main className="flex min-h-0 flex-1 flex-col">
        {(backendError || missingKeys) && (
          <div className="border-b border-amber-200 bg-amber-50 px-6 py-2 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
            {backendError ??
              `Add ${[
                !health?.pinecone_configured && "PINECONE_API_KEY",
                !health?.llm_configured && "ANTHROPIC_API_KEY",
              ]
                .filter(Boolean)
                .join(" and ")} to backend/.env, then restart the backend.`}
          </div>
        )}
        <div className="min-h-0 flex-1">
          <ChatWindow readyCount={readyCount} scopeIds={selected.size ? [...selected] : null} />
        </div>
      </main>
    </div>
  );
}
