import type { Source } from "@/lib/api";

export function sourceLocation(source: Source): string {
  if (source.page) return `page ${source.page}`;
  if (source.slide) return `slide ${source.slide}`;
  return "";
}

export default function SourceCard({ source, onClose }: { source: Source; onClose: () => void }) {
  const where = sourceLocation(source);
  return (
    <div className="mt-3 rounded-lg border border-indigo-200 bg-indigo-50/60 p-3 text-sm dark:border-indigo-900 dark:bg-indigo-950/30">
      <div className="mb-2 flex items-start justify-between gap-2">
        <p className="font-medium">
          [{source.n}] {source.filename}
          {where && <span className="font-normal text-stone-500 dark:text-stone-400"> · {where}</span>}
        </p>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close source"
          className="text-stone-400 hover:text-stone-700 dark:hover:text-stone-200"
        >
          ×
        </button>
      </div>
      <p className="max-h-48 overflow-y-auto whitespace-pre-wrap text-stone-700 dark:text-stone-300">{source.text}</p>
    </div>
  );
}
