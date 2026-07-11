// components/RouteBadge.tsx
"use client";

import { motion } from "framer-motion";
import { Cpu, Cloud } from "lucide-react";
import type { Route } from "@/types/chat";

interface Props {
  route: Route;
  size?: "sm" | "md";
}

export default function RouteBadge({ route, size = "md" }: Props) {
  const isLocal = route === "LOCAL";
  const isSmall = size === "sm";

  return (
    <motion.span
      initial={{ scale: 0.7, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className={`inline-flex items-center gap-1.5 font-semibold rounded-full border ${
        isSmall ? "text-[10px] px-2 py-0.5" : "text-xs px-3 py-1"
      } ${
        isLocal
          ? "text-green-400 border-green-500/30 bg-green-500/10"
          : "text-blue-400 border-blue-500/30 bg-blue-500/10"
      }`}
    >
      {isLocal ? (
        <Cpu className={isSmall ? "w-3 h-3" : "w-3.5 h-3.5"} />
      ) : (
        <Cloud className={isSmall ? "w-3 h-3" : "w-3.5 h-3.5"} />
      )}
      {route}
    </motion.span>
  );
}
