// components/InputBar.tsx
"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { motion } from "framer-motion";
import { Send, Loader2 } from "lucide-react";

interface Props {
  onSend: (query: string) => void;
  disabled: boolean;
}

const EXAMPLE_QUERIES = [
  "Install nginx on Ubuntu",
  "Explain quantum entanglement",
  "Write a Python web scraper",
  "Translate hello to French",
  "Debug this SQL query: SELECT * FROM users WHERE id = 1",
];

export default function InputBar({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
  };

  const handleExample = (q: string) => {
    setValue(q);
    textareaRef.current?.focus();
  };

  return (
    <div className="px-4 pb-4 pt-2">
      {/* Example pills */}
      {value === "" && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => handleExample(q)}
              className="text-[11px] text-slate-400 px-2.5 py-1 rounded-lg bg-white/4 border border-white/8 hover:border-purple-500/40 hover:text-purple-300 transition-all duration-150"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input box */}
      <motion.div
        className="input-glow flex items-end gap-3 p-3 rounded-2xl border border-white/8"
        style={{ background: "rgba(255,255,255,0.04)" }}
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <textarea
          ref={textareaRef}
          id="query-input"
          value={value}
          onChange={(e) => { setValue(e.target.value); handleInput(); }}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything… (Enter to send, Shift+Enter for new line)"
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-600 resize-none outline-none leading-relaxed"
          style={{ minHeight: 28, maxHeight: 140 }}
        />

        <button
          id="send-button"
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="send-btn w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
        >
          {disabled ? (
            <Loader2 className="w-4 h-4 text-white animate-spin" />
          ) : (
            <Send className="w-4 h-4 text-white" />
          )}
        </button>
      </motion.div>

      <p className="text-center text-[10px] text-slate-700 mt-2">
        Press Enter to send · Shift+Enter for new line
      </p>
    </div>
  );
}
