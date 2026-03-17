import { getInitData } from "./telegram";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const initData = getInitData();
  const headers = new Headers(init?.headers ?? {});
  headers.set("Content-Type", "application/json");
  if (initData) headers.set("X-Telegram-Init-Data", initData);

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export type Me = { id: number; username: string | null; balance: number };
export type MatchStatus = "scheduled" | "live" | "finished";
export type Match = {
  id: number;
  team1: string;
  team2: string;
  start_time: string;
  status: MatchStatus;
  winner: string | null;
  coef_team1: number;
  coef_team2: number;
};

export type BetCreate = { match_id: number; team: string; amount: number };
export type Bet = { id: number; match_id: number; team: string; amount: number; coef: number };
export type BetWithMatch = {
  id: number;
  match_id: number;
  team: string;
  amount: number;
  coef: number;
  match_team1: string;
  match_team2: string;
  match_start_time: string;
  match_status: string;
  match_winner: string | null;
};

export const api = {
  me: () => request<Me>("/me"),
  matches: (status?: MatchStatus) =>
    request<Match[]>(`/matches${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  placeBet: (payload: BetCreate) =>
    request<Bet>("/bets", { method: "POST", body: JSON.stringify(payload) }),
  myBets: () => request<BetWithMatch[]>("/bets/mine"),
};

