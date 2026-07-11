// components/StatsDashboard.tsx
"use client";

import { motion } from "framer-motion";
import { BarChart3, Cpu, Cloud, Target, Clock, TrendingUp } from "lucide-react";
import type { RouteStats } from "@/types/chat";

interface Props {
  stats: RouteStats;
}

// Simple SVG donut chart
function DonutChart({ local, cloud }: { local: number; cloud: number }) {
  const total = local + cloud;
  const r = 44;
  const cx = 56;
  const cy = 56;
  const circumference = 2 * Math.PI * r;

  const localPct  = total > 0 ? local  / total : 0.5;
  const cloudPct  = total > 0 ? cloud  / total : 0.5;

  const localDash  = localPct  * circumference;
  const cloudDash  = cloudPct  * circumference;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative">
        <svg width="112" height="112" viewBox="0 0 112 112">
          {/* Track */}
          <circle cx={cx} cy={cy} r={r} fill="none"
            stroke="rgba(255,255,255,0.05)" strokeWidth="14" />

          {/* LOCAL segment */}
          <motion.circle
            cx={cx} cy={cy} r={r} fill="none"
            stroke="#22c55e" strokeWidth="14"
            strokeDasharray={`${localDash} ${circumference}`}
            strokeDashoffset={circumference * 0.25}
            strokeLinecap="butt"
            initial={{ strokeDasharray: `0 ${circumference}` }}
            animate={{ strokeDasharray: `${localDash} ${circumference - localDash}` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />

          {/* CLOUD segment */}
          <motion.circle
            cx={cx} cy={cy} r={r} fill="none"
            stroke="#3b82f6" strokeWidth="14"
            strokeDasharray={`${cloudDash} ${circumference}`}
            strokeDashoffset={circumference * 0.25 - localDash}
            strokeLinecap="butt"
            initial={{ strokeDasharray: `0 ${circumference}` }}
            animate={{ strokeDasharray: `${cloudDash} ${circumference - cloudDash}` }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
          />

          {/* Center text */}
          <text x={cx} y={cy - 4} textAnchor="middle"
            fill="#f1f5f9" fontSize="18" fontWeight="700" fontFamily="Inter">
            {total}
          </text>
          <text x={cx} y={cy + 14} textAnchor="middle"
            fill="#64748b" fontSize="10" fontFamily="Inter">
            queries
          </text>
        </svg>
      </div>

      {/* Legend */}
      <div className="flex gap-4 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-slate-400">LOCAL</span>
          <span className="text-slate-300 font-semibold">{local}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span className="text-slate-400">CLOUD</span>
          <span className="text-slate-300 font-semibold">{cloud}</span>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
  color: string;
}) {
  return (
    <div className="stat-card">
      <div className="flex items-start justify-between mb-1">
        <span className="text-[11px] text-slate-500 font-medium">{label}</span>
        <Icon className="w-3.5 h-3.5 flex-shrink-0" style={{ color }} />
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
      {sub && <p className="text-[10px] text-slate-600 mt-0.5">{sub}</p>}
    </div>
  );
}

export default function StatsDashboard({ stats }: Props) {
  const avgConf = Math.round(stats.avgConfidence * 100);
  const avgLat  = stats.avgLatency < 1000
    ? `${Math.round(stats.avgLatency)} ms`
    : `${(stats.avgLatency / 1000).toFixed(1)} s`;

  return (
    <motion.div
      initial={{ x: 40, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut", delay: 0.1 }}
      className="flex flex-col h-full overflow-y-auto"
      style={{ width: 280 }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-4 border-b border-white/5">
        <BarChart3 className="w-4 h-4 text-purple-400" />
        <h2 className="text-sm font-semibold text-white">Live Statistics</h2>
        {stats.total > 0 && (
          <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-purple-500/15 border border-purple-500/25 text-purple-300">
            LIVE
          </span>
        )}
      </div>

      <div className="flex-1 px-3 py-4 space-y-4">
        {/* Donut chart */}
        <div className="glass-sm p-4 flex flex-col items-center">
          <p className="text-[11px] text-slate-500 font-semibold uppercase tracking-widest mb-3">
            Route Distribution
          </p>
          <DonutChart local={stats.local} cloud={stats.cloud} />
        </div>

        {/* Stat cards grid */}
        <div className="grid grid-cols-2 gap-2">
          <StatCard
            icon={Target}
            label="Total Queries"
            value={stats.total.toString()}
            color="#7c3aed"
          />
          <StatCard
            icon={TrendingUp}
            label="Avg Confidence"
            value={stats.total > 0 ? `${avgConf}%` : "—"}
            sub={avgConf >= 90 ? "High" : avgConf >= 70 ? "Medium" : "Low"}
            color={avgConf >= 90 ? "#22c55e" : avgConf >= 70 ? "#eab308" : "#ef4444"}
          />
          <StatCard
            icon={Cpu}
            label="LOCAL Routed"
            value={stats.local.toString()}
            sub={stats.total > 0 ? `${Math.round((stats.local / stats.total) * 100)}% of total` : undefined}
            color="#22c55e"
          />
          <StatCard
            icon={Cloud}
            label="CLOUD Routed"
            value={stats.cloud.toString()}
            sub={stats.total > 0 ? `${Math.round((stats.cloud / stats.total) * 100)}% of total` : undefined}
            color="#3b82f6"
          />
        </div>

        {/* Latency */}
        <div className="stat-card">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] text-slate-500 font-medium">Avg Response Time</span>
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <p className="text-xl font-bold text-white">{stats.total > 0 ? avgLat : "—"}</p>
          <p className="text-[10px] text-slate-600 mt-0.5">
            Includes LLM generation time
          </p>
        </div>

        {/* Cost savings note */}
        {stats.local > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl p-3 bg-green-500/8 border border-green-500/20"
          >
            <p className="text-[11px] text-green-400 font-medium mb-0.5">💰 Cost Efficiency</p>
            <p className="text-[11px] text-slate-400">
              {stats.local} queries handled locally — saving cloud API costs.
            </p>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
