// components/Sidebar.tsx
"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Plus, MessageSquare, Cpu, Trash2, ChevronRight } from "lucide-react";
import type { Conversation } from "@/types/chat";

interface Props {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export default function Sidebar({ conversations, activeId, onSelect, onNew, onDelete }: Props) {
  return (
    <motion.aside
      initial={{ x: -280, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex flex-col h-full"
      style={{ width: 260 }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-5 border-b border-white/5">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center"
             style={{ background: "linear-gradient(135deg, #7c3aed, #06b6d4)" }}>
          <Cpu className="w-4 h-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-tight">AI Router</p>
          <p className="text-[10px] text-slate-500">Intelligent LLM Selection</p>
        </div>
      </div>

      {/* New chat button */}
      <div className="px-3 pt-4 pb-2">
        <button
          onClick={onNew}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium text-white transition-all duration-200 hover:opacity-90 active:scale-95"
          style={{ background: "linear-gradient(135deg, #7c3aed, #5b21b6)" }}
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* History list */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest px-2 mb-2">
          History
        </p>

        <AnimatePresence>
          {conversations.length === 0 ? (
            <p className="text-xs text-slate-600 text-center py-8 px-4">
              No conversations yet.<br />Start a new chat above.
            </p>
          ) : (
            conversations
              .slice()
              .reverse()
              .map((conv) => (
                <motion.div
                  key={conv.id}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.2 }}
                  className={`sidebar-item flex items-center gap-2.5 group ${
                    activeId === conv.id ? "active" : ""
                  }`}
                  onClick={() => onSelect(conv.id)}
                >
                  <MessageSquare className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                  <span className="text-xs text-slate-300 flex-1 truncate">
                    {conv.title}
                  </span>
                  <button
                    onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:text-red-400 text-slate-500"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                  {activeId === conv.id && (
                    <ChevronRight className="w-3 h-3 text-purple-400 flex-shrink-0" />
                  )}
                </motion.div>
              ))
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/5">
        <p className="text-[10px] text-slate-600 text-center">
          AMD Developer Hackathon — ACT II
        </p>
      </div>
    </motion.aside>
  );
}
