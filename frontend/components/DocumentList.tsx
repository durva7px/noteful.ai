"use client";

import type { DocStatus, DocumentInfo } from "@/lib/api";

const STATUS_STYLES: Record<DocStatus, string> = {
  processing: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  ready: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
};

interface Props {
  documents: DocumentInfo[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function DocumentList({ documents, selected, onToggle, onDelete }: Props) {
  if (!documents.length) {
    return <p className="px-1 text-sm text-stone-500 dark:text-stone-400">No documents yet.</p>;
  }

  return (
    <ul className="space-y-2">
      {documents.map((doc) => (
        <li
          key={doc.id}
          className="group rounded-lg border border-stone-200 bg-white p-3 dark:border-stone-800 dark:bg-stone-900"
        >
          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              aria-label={`Use ${doc.filename} in chat`}
              className="mt-1 accent-indigo-600"
              checked={selected.has(doc.id)}
              disabled={doc.status !== "ready"}
              onChange={() => onToggle(doc.id)}
            />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium" title={doc.filename}>
                {doc.filename}
              </p>
              <div className="mt-1 flex items-center gap-2 text-xs text-stone-500 dark:text-stone-400">
                <span className={`rounded-full px-2 py-0.5 font-medium ${STATUS_STYLES[doc.status]}`}>
                  {doc.status}
                </span>
                {doc.status === "ready" && <span>{doc.chunk_count} chunks</span>}
              </div>
              {doc.error && (
                <p className="mt-1 text-xs text-red-600 dark:text-red-400" title={doc.error}>
                  {doc.error}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={() => onDelete(doc.id)}
              aria-label={`Delete ${doc.filename}`}
              className="rounded p-1 text-stone-400 opacity-0 transition hover:bg-stone-100 hover:text-red-600 group-hover:opacity-100 focus:opacity-100 dark:hover:bg-stone-800"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 6h18M8 6V4h8v2m-9 0 1 14h8l1-14" />
              </svg>
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
