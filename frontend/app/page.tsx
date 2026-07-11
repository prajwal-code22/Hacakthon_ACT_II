// app/page.tsx — Main AI Router interface
"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, Cpu } from "lucide-react";

import Sidebar from "@/components/Sidebar";
import ChatMessage from "@/components/ChatMessage";
import InputBar from "@/components/InputBar";
import StatusIndicator from "@/components/StatusIndicator";
import StatsDashboard from "@/components/StatsDashboard";
import LoadingSpinner from "@/components/LoadingSpinner";

import { predict } from "@/services/api";
import type { Message, Conversation, RouteStats } from "@/types/chat";

// ── Helpers ────────────────────────────────────────────────────────────────
const uid = () => Math.random().toString(36).slice(2);

function createConversation(): Conversation {
  return { id: uid(), title: "New Chat", createdAt: new Date(), messages: [] };
}

// ── Page ───────────────────────────────────────────────────────────────────
export default function Page() {
  const [conversations, setConversations] = useState<Conversation[]>([createConversation()]);
  const [activeId, setActiveId] = useState<string>(conversations[0].id);
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState<RouteStats>({
    total: 0, local: 0, cloud: 0, avgConfidence: 0, avgLatency: 0,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversations, isLoading]);

  // Active conversation
  const activeConv = conversations.find((c) => c.id === activeId) ?? conversations[0];

  // Update a conversation immutably
  const updateConv = useCallback((id: string, updater: (c: Conversation) => Conversation) => {
    setConversations((prev) => prev.map((c) => (c.id === id ? updater(c) : c)));
  }, []);

  // Send a query
  const handleSend = async (query: string) => {
    if (isLoading) return;

    const userMsg: Message = {
      id: uid(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };

    // Append user message; set conversation title from first query
    updateConv(activeId, (c) => ({
      ...c,
      title: c.messages.length === 0 ? query.slice(0, 40) : c.title,
      messages: [...c.messages, userMsg],
    }));

    setIsLoading(true);

    try {
      const data = await predict(query);

      const assistantMsg: Message = {
        id: uid(),
        role: "assistant",
        content: data.answer,
        timestamp: new Date(),
        route:      data.route,
        confidence: data.confidence,
        intent:     data.intent,
        complexity: data.complexity,
        latency_ms: data.latency_ms,
      };

      updateConv(activeId, (c) => ({
        ...c,
        messages: [...c.messages, assistantMsg],
      }));

      // Update live stats
      setStats((prev) => {
        const newTotal = prev.total + 1;
        const newLocal = prev.local + (data.route === "LOCAL" ? 1 : 0);
        const newCloud = prev.cloud + (data.route === "CLOUD" ? 1 : 0);
        const newConf  = (prev.avgConfidence * prev.total + data.confidence) / newTotal;
        const newLat   = (prev.avgLatency   * prev.total + data.latency_ms) / newTotal;
        return {
          total: newTotal,
          local: newLocal,
          cloud: newCloud,
          avgConfidence: newConf,
          avgLatency:    newLat,
        };
      });
    } catch (err: unknown) {
      const errorMsg: Message = {
        id: uid(),
        role: "assistant",
        content:
          "⚠️ **Failed to reach the backend.**\n\n" +
          "Make sure the FastAPI server is running:\n" +
          "```\ncd backend\nuvicorn app:app --reload\n```",
        timestamp: new Date(),
      };
      updateConv(activeId, (c) => ({ ...c, messages: [...c.messages, errorMsg] }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    const conv = createConversation();
    setConversations((prev) => [...prev, conv]);
    setActiveId(conv.id);
  };

  const handleDeleteConv = (id: string) => {
    setConversations((prev) => {
      const next = prev.filter((c) => c.id !== id);
      if (next.length === 0) {
        const fresh = createConversation();
        setActiveId(fresh.id);
        return [fresh];
      }
      if (id === activeId) setActiveId(next[next.length - 1].id);
      return next;
    });
  };

  return (
    <div className="flex h-screen overflow-hidden">

      {/* ── Left Sidebar ─────────────────────────────────────────────── */}
      <div className="flex-shrink-0 border-r border-white/5"
           style={{ background: "rgba(6,11,20,0.95)" }}>
        <Sidebar
          conversations={conversations}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={handleNewChat}
          onDelete={handleDeleteConv}
        />
      </div>

      {/* ── Center Chat ───────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Top bar */}
        <header className="flex items-center justify-between px-6 py-3.5 border-b border-white/5 flex-shrink-0"
                style={{ background: "rgba(6,11,20,0.9)", backdropFilter: "blur(12px)" }}>
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                 style={{ background: "linear-gradient(135deg, #7c3aed, #06b6d4)" }}>
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold gradient-text">AI Router</h1>
              <p className="text-[10px] text-slate-600 hidden sm:block">
                {activeConv.title === "New Chat" ? "Awaiting your query…" : activeConv.title}
              </p>
            </div>
          </div>
          <StatusIndicator />
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto py-4">
          {activeConv.messages.length === 0 ? (
            <EmptyState />
          ) : (
            <>
              <AnimatePresence initial={false}>
                {activeConv.messages.map((msg, i) => (
                  <ChatMessage key={msg.id} message={msg} index={i} />
                ))}
              </AnimatePresence>
              {isLoading && <LoadingSpinner />}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-white/5 flex-shrink-0"
             style={{ background: "rgba(6,11,20,0.9)", backdropFilter: "blur(12px)" }}>
          <InputBar onSend={handleSend} disabled={isLoading} />
        </div>
      </div>

      {/* ── Right Stats Dashboard ─────────────────────────────────────── */}
      <div className="flex-shrink-0 border-l border-white/5"
           style={{ background: "rgba(6,11,20,0.95)" }}>
        <StatsDashboard stats={stats} />
      </div>
    </div>
  );
}

// ── Empty state ────────────────────────────────────────────────────────────
function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center justify-center h-full px-8 text-center"
    >
      <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
           style={{ background: "linear-gradient(135deg, #7c3aed22, #06b6d422)", border: "1px solid rgba(124,58,237,0.2)" }}>
        <Cpu className="w-8 h-8 text-purple-400" />
      </div>

      <h2 className="text-2xl font-bold gradient-text mb-2">AI Router</h2>
      <p className="text-slate-400 text-sm max-w-sm leading-relaxed mb-6">
        Automatically routes your queries to the most efficient AI model — 
        local Gemma for simple tasks, Fireworks cloud for complex reasoning.
      </p>

      {/* Feature pills */}
      <div className="flex flex-wrap justify-center gap-2 max-w-xs">
        {[
          { label: "Local Gemma 3", color: "#22c55e" },
          { label: "Cloud Llama 3.1", color: "#3b82f6" },
          { label: "62 Intent Classes", color: "#7c3aed" },
          { label: "Complexity Scoring", color: "#06b6d4" },
        ].map(({ label, color }) => (
          <span key={label}
            className="text-xs px-3 py-1.5 rounded-full border"
            style={{ color, borderColor: `${color}40`, background: `${color}10` }}>
            {label}
          </span>
        ))}
      </div>

      <p className="text-slate-600 text-xs mt-8">
        Type a query below or pick an example to get started ↓
      </p>
    </motion.div>
  );
}
