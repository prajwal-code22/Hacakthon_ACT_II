// types/chat.ts — TypeScript interfaces for the AI Router frontend

export type Route = "LOCAL" | "CLOUD";

export interface PredictResponse {
  route: Route;
  confidence: number;   // [0, 1]
  intent: string;
  complexity: number;   // [0, 1]
  answer: string;
  latency_ms: number;
}

export interface RouteResponse {
  route: Route;
  confidence: number;
  intent: string;
  complexity: number;
  latency_ms: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  // Only on assistant messages
  route?: Route;
  confidence?: number;
  intent?: string;
  complexity?: number;
  latency_ms?: number;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: Date;
  messages: Message[];
}

export interface RouteStats {
  total: number;
  local: number;
  cloud: number;
  avgConfidence: number;
  avgLatency: number;
}
