// components/StatusIndicator.tsx
"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Wifi, WifiOff, Server, Cpu, Cloud } from "lucide-react";
import { healthCheck } from "@/services/api";

export default function StatusIndicator() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");
  const [device, setDevice] = useState<string>("—");

  useEffect(() => {
    const check = async () => {
      try {
        const data = await healthCheck();
        setStatus("online");
        setDevice(data.device ?? "cpu");
      } catch {
        setStatus("offline");
      }
    };
    check();
    const interval = setInterval(check, 30_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-3"
    >
      {/* Device badge */}
      <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-slate-400 px-2.5 py-1 rounded-lg bg-white/5 border border-white/8">
        <Cpu className="w-3 h-3" />
        <span className="uppercase font-medium">{device}</span>
      </div>

      {/* Model indicators */}
      <div className="hidden md:flex items-center gap-2">
        <div className="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400">
          <Cpu className="w-3 h-3" />
          <span>Gemma 3</span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
          <Cloud className="w-3 h-3" />
          <span>Llama 3.1</span>
        </div>
      </div>

      {/* Connection status */}
      <div className={`flex items-center gap-1.5 text-[11px] px-2.5 py-1.5 rounded-lg border ${
        status === "online"
          ? "bg-green-500/10 border-green-500/20 text-green-400"
          : status === "offline"
          ? "bg-red-500/10 border-red-500/20 text-red-400"
          : "bg-slate-500/10 border-slate-500/20 text-slate-400"
      }`}>
        {status === "online" ? (
          <>
            <div className="status-dot w-1.5 h-1.5 rounded-full bg-green-400" />
            <span className="hidden sm:inline">Backend Online</span>
          </>
        ) : status === "offline" ? (
          <>
            <WifiOff className="w-3 h-3" />
            <span className="hidden sm:inline">Backend Offline</span>
          </>
        ) : (
          <>
            <Server className="w-3 h-3 animate-pulse" />
            <span className="hidden sm:inline">Connecting…</span>
          </>
        )}
      </div>
    </motion.div>
  );
}
