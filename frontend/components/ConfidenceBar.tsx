// components/ConfidenceBar.tsx
"use client";

import { motion } from "framer-motion";

interface Props {
  value: number; // [0, 1]
  showLabel?: boolean;
}

function getColor(value: number): string {
  if (value >= 0.9) return "#22c55e";   // green
  if (value >= 0.7) return "#eab308";   // yellow
  return "#ef4444";                      // red
}

function getLabel(value: number): string {
  if (value >= 0.9) return "High";
  if (value >= 0.7) return "Medium";
  return "Low";
}

export default function ConfidenceBar({ value, showLabel = true }: Props) {
  const pct = Math.round(value * 100);
  const color = getColor(value);

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-[11px] text-slate-400 font-medium">Confidence</span>
          <span className="text-[11px] font-bold" style={{ color }}>
            {pct}% &middot; {getLabel(value)}
          </span>
        </div>
      )}
      <div className="confidence-track">
        <motion.div
          className="confidence-fill"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1], delay: 0.1 }}
          style={{ background: `linear-gradient(90deg, ${color}cc, ${color})` }}
        />
      </div>
    </div>
  );
}
