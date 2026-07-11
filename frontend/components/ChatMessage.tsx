// components/ChatMessage.tsx
"use client";

import { motion } from "framer-motion";
import { Bot, User, Clock, Zap } from "lucide-react";
import RouteBadge from "./RouteBadge";
import ConfidenceBar from "./ConfidenceBar";
import type { Message } from "@/types/chat";

interface Props {
  message: Message;
  index: number;
}

/** Simple text renderer: wraps ``` blocks in <pre><code> */
function renderAnswer(text: string) {
  const parts = text.split(/(```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    if (part.startsWith("```")) {
      const content = part.replace(/^```[^\n]*\n?/, "").replace(/```$/, "");
      return (
        <pre key={i}>
          <code>{content}</code>
        </pre>
      );
    }
    // Inline code: `...`
    const inlineParts = part.split(/(`[^`]+`)/g);
    return (
      <span key={i}>
        {inlineParts.map((seg, j) => {
          if (seg.startsWith("`") && seg.endsWith("`")) {
            return <code key={j}>{seg.slice(1, -1)}</code>;
          }
          return <span key={j} style={{ whiteSpace: "pre-wrap" }}>{seg}</span>;
        })}
      </span>
    );
  });
}

export default function ChatMessage({ message, index }: Props) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut", delay: index * 0.04 }}
      className={`flex items-start gap-3 px-4 py-2 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? "bg-purple-600" : ""
        }`}
        style={
          isUser
            ? undefined
            : { background: "linear-gradient(135deg, #7c3aed, #06b6d4)" }
        }
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Content */}
      {isUser ? (
        <div className="user-bubble">
          <p className="text-sm text-white leading-relaxed">{message.content}</p>
          <p className="text-[10px] text-purple-300/70 mt-1.5">
            {message.timestamp.toLocaleTimeString()}
          </p>
        </div>
      ) : (
        <div className="ai-card">
          {/* Header row: badges */}
          {message.route && (
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <RouteBadge route={message.route} />

              {/* Intent badge */}
              <span className="text-[11px] px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-slate-400 font-medium">
                {message.intent?.replace(/_/g, " ")}
              </span>
            </div>
          )}

          {/* Answer text */}
          <div className="answer-text text-sm text-slate-200 leading-relaxed mb-3">
            {renderAnswer(message.content)}
          </div>

          {/* Confidence bar */}
          {message.confidence !== undefined && (
            <div className="mb-3">
              <ConfidenceBar value={message.confidence} />
            </div>
          )}

          {/* Stats row */}
          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-white/5">
            {message.complexity !== undefined && (
              <div className="flex items-center gap-1.5">
                <Zap className="w-3 h-3 text-slate-500" />
                <span className="text-[11px] text-slate-400">
                  Complexity{" "}
                  <span className="text-slate-300 font-medium">
                    {Math.round(message.complexity * 100)}%
                  </span>
                </span>
              </div>
            )}
            {message.latency_ms !== undefined && (
              <div className="flex items-center gap-1.5">
                <Clock className="w-3 h-3 text-slate-500" />
                <span className="text-[11px] text-slate-400">
                  {message.latency_ms < 1000
                    ? `${Math.round(message.latency_ms)} ms`
                    : `${(message.latency_ms / 1000).toFixed(1)} s`}
                </span>
              </div>
            )}
            <span className="text-[10px] text-slate-600 ml-auto">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
        </div>
      )}
    </motion.div>
  );
}
