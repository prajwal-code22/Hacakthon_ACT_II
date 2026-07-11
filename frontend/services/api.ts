// services/api.ts — Axios client for the AI Router backend

import axios from "axios";
import type { PredictResponse, RouteResponse } from "@/types/chat";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 180_000, // 3 min — LLM calls can be slow
  headers: { "Content-Type": "application/json" },
});

/** Send a query and get the full prediction + LLM answer. */
export async function predict(query: string): Promise<PredictResponse> {
  const { data } = await client.post<PredictResponse>("/predict", { query });
  return data;
}

/** Get only the routing decision without calling any LLM. */
export async function routeOnly(query: string): Promise<RouteResponse> {
  const { data } = await client.post<RouteResponse>("/route", { query });
  return data;
}

/** Ping the health endpoint. */
export async function healthCheck(): Promise<{ status: string; device: string }> {
  const { data } = await client.get("/health");
  return data;
}
