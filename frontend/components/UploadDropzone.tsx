"use client";

import { useRef, useState } from "react";
import { ACCEPTED_TYPES, uploadDocuments } from "@/lib/api";

export default function UploadDropzone({ onUploaded }: { onUploaded: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFiles(list: FileList | null) {
    const files = Array.from(list ?? []);
    if (!files.length) return;
    const bad = files.find((f) => !ACCEPTED_TYPES.some((ext) => f.name.toLowerCase().endsWith(ext)));
    if (bad) {
      setError(`${bad.name}: unsupported type. Use ${ACCEPTED_TYPES.join(", ")}.`);
      return;
    }
    setError(null);
    setUploading(true);
    try {
      await uploadDocuments(files);
      onUploaded();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        disabled={uploading}
        className={`w-full rounded-xl border-2 border-dashed px-4 py-6 text-center text-sm transition-colors ${
          dragging
            ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/40"
            : "border-stone-300 hover:border-indigo-400 hover:bg-stone-100 dark:border-stone-700 dark:hover:bg-stone-800/60"
        } disabled:cursor-wait disabled:opacity-60`}
      >
        <span className="block font-medium">{uploading ? "Uploading…" : "Drop study files here"}</span>
        <span className="mt-1 block text-xs text-stone-500 dark:text-stone-400">
          or click to browse · PDF, PPTX, DOCX, TXT, MD
        </span>
      </button>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_TYPES.join(",")}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      {error && <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
