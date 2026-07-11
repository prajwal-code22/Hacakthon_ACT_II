// components/LoadingSpinner.tsx
"use client";

import { motion } from "framer-motion";
import { Bot } from "lucide-react";

export default function LoadingSpinner() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className="flex items-start gap-3 px-4 py-2"
    >
      {/* Avatar */}
      <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
           style={{ background: "linear-gradient(135deg, #7c3aed, #06b6d4)" }}>
        <Bot className="w-4 h-4 text-white" />
      </div>

      {/* Typing bubble */}
      <div className="ai-card py-4 px-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs text-slate-400">Thinking</span>
        </div>
        <div className="flex gap-1.5 items-center h-5">
          <div className="typing-dot w-2 h-2 rounded-full bg-purple-400" />
          <div className="typing-dot w-2 h-2 rounded-full bg-purple-400" />
          <div className="typing-dot w-2 h-2 rounded-full bg-purple-400" />
        </div>
      </div>
    </motion.div>
  );
}
