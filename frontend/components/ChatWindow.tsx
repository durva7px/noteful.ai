"use client";

import { useEffect, useRef, useState } from "react";
import { streamChat, type ChatTurn } from "@/lib/api";
import MessageBubble, { type Message } from "./MessageBubble";

interface Props {
  readyCount: number;
  scopeIds: string[] | null;
}

export default function ChatWindow({ readyCount, scopeIds }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  function updateLast(patch: (m: Message) => Message) {
    setMessages((prev) => [...prev.slice(0, -1), patch(prev[prev.length - 1])]);
  }

  async function ask(question: string) {
    const history: ChatTurn[] = messages
      .filter((m) => m.content && !m.error)
      .map(({ role, content }) => ({ role, content }));

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "", streaming: true },
    ]);
    setBusy(true);
    abortRef.current = new AbortController();

    try {
      await streamChat(
        { question, history, doc_ids: scopeIds },
        {
          onSources: (sources) => updateLast((m) => ({ ...m, sources })),
          onToken: (token) => updateLast((m) => ({ ...m, content: m.content + token })),
        },
        abortRef.current.signal,
      );
    } catch (e) {
      if (!(e instanceof DOMException && e.name === "AbortError")) {
        updateLast((m) => ({ ...m, error: e instanceof Error ? e.message : "Something went wrong" }));
      }
    } finally {
      updateLast((m) => ({ ...m, streaming: false }));
      setBusy(false);
    }
  }

  function submit() {
    const question = input.trim();
    if (!question || busy) return;
    setInput("");
    ask(question);
  }

  function retry() {
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUser || busy) return;
    setMessages((prev) => prev.slice(0, -2));
    ask(lastUser.content);
  }

  const last = messages[messages.length - 1];

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-3xl flex-col gap-5 px-4 py-6 sm:px-6">
          {messages.length === 0 && (
            <div className="mt-20 text-center">
              <h2 className="text-2xl font-semibold">What do you want to understand?</h2>
              <p className="mt-2 text-stone-500 dark:text-stone-400">
                {readyCount
                  ? "Ask about any concept in your study material. Answers cite the page or slide they came from."
                  : "Upload your study material on the left to get started."}
              </p>
            </div>
          )}
          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} />
          ))}
          {last?.error && !busy && (
            <button
              type="button"
              onClick={retry}
              className="self-start text-sm font-medium text-indigo-600 hover:underline dark:text-indigo-400"
            >
              Retry
            </button>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t border-stone-200 bg-stone-50/80 px-4 py-4 backdrop-blur sm:px-6 dark:border-stone-800 dark:bg-stone-950/80">
        <form
          className="mx-auto flex max-w-3xl items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            rows={1}
            placeholder={readyCount ? "Explain the Calvin cycle in simple terms…" : "Upload a document first"}
            disabled={!readyCount}
            className="max-h-40 min-h-11 flex-1 resize-none rounded-xl border border-stone-300 bg-white px-4 py-2.5 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50 dark:border-stone-700 dark:bg-stone-900"
          />
          {busy ? (
            <button
              type="button"
              onClick={() => abortRef.current?.abort()}
              className="h-11 rounded-xl border border-stone-300 px-4 text-sm font-medium hover:bg-stone-100 dark:border-stone-700 dark:hover:bg-stone-800"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim() || !readyCount}
              className="h-11 rounded-xl bg-indigo-600 px-5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
            >
              Ask
            </button>
          )}
        </form>
        {scopeIds && (
          <p className="mx-auto mt-2 max-w-3xl text-xs text-stone-500 dark:text-stone-400">
            Searching {scopeIds.length} selected document{scopeIds.length === 1 ? "" : "s"}
          </p>
        )}
      </div>
    </div>
  );
}
