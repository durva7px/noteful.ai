"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import type { Source } from "@/lib/api";
import SourceCard, { sourceLocation } from "./SourceCard";

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  error?: string;
  streaming?: boolean;
}

/** Turn [1] and [1, 2] citations into links that the renderer shows as chips. */
function linkCitations(text: string): string {
  return text.replace(/\[(\d+(?:\s*,\s*\d+)*)\](?!\()/g, (_, nums: string) =>
    nums
      .split(",")
      .map((n) => `[${n.trim()}](#cite-${n.trim()})`)
      .join(""),
  );
}

export default function MessageBubble({ message }: { message: Message }) {
  const [active, setActive] = useState<number | null>(null);

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-2.5 text-white">
          {message.content}
        </div>
      </div>
    );
  }

  const sources = message.sources ?? [];
  const activeSource = sources.find((s) => s.n === active);

  return (
    <div className="max-w-[90%]">
      <div className="prose prose-stone max-w-none overflow-x-auto rounded-2xl rounded-bl-sm border border-stone-200 bg-white px-4 py-3 dark:prose-invert dark:border-stone-800 dark:bg-stone-900">
        {message.content ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
            components={{
              a: ({ href, children }) => {
                const match = href?.match(/^#cite-(\d+)$/);
                if (!match) {
                  return (
                    <a href={href} target="_blank" rel="noreferrer">
                      {children}
                    </a>
                  );
                }
                const n = Number(match[1]);
                const known = sources.some((s) => s.n === n);
                return (
                  <button
                    type="button"
                    onClick={() => known && setActive(active === n ? null : n)}
                    className={`mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 align-text-top text-[11px] font-semibold no-underline ${
                      active === n
                        ? "bg-indigo-600 text-white"
                        : "bg-indigo-100 text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/60 dark:text-indigo-200"
                    }`}
                  >
                    {n}
                  </button>
                );
              },
            }}
          >
            {linkCitations(message.content)}
          </ReactMarkdown>
        ) : message.streaming ? (
          <span className="inline-flex gap-1 py-1" aria-label="Thinking">
            <span className="h-2 w-2 animate-bounce rounded-full bg-stone-400 [animation-delay:-0.3s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-stone-400 [animation-delay:-0.15s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-stone-400" />
          </span>
        ) : null}
        {message.error && <p className="text-sm text-red-600 dark:text-red-400">{message.error}</p>}
      </div>

      {activeSource && <SourceCard source={activeSource} onClose={() => setActive(null)} />}

      {sources.length > 0 && !message.streaming && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {sources.map((s) => (
            <button
              key={s.n}
              type="button"
              onClick={() => setActive(active === s.n ? null : s.n)}
              className="rounded-md border border-stone-200 bg-white px-2 py-1 text-xs text-stone-600 hover:border-indigo-300 dark:border-stone-800 dark:bg-stone-900 dark:text-stone-300"
            >
              [{s.n}] {s.filename}
              {sourceLocation(s) && ` · ${sourceLocation(s)}`}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
