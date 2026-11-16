/**
 * MediSync AI — Auth helper utilities
 * Thin wrappers around localStorage token handling.
 */

import { type UserRole } from "@/types";

interface JWTPayload {
  sub: string;
  role: UserRole;
  exp: number;
}

export function saveToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", token);
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function removeToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
  }
}

/** Decode JWT payload WITHOUT verification — client-side display only. */
export function getDecodedToken(): JWTPayload | null {
  const token = getToken();
  if (!token) return null;
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const payload = JSON.parse(atob(parts[1])) as JWTPayload;
    return payload;
  } catch {
    return null;
  }
}

export function getCurrentRole(): UserRole | null {
  return getDecodedToken()?.role ?? null;
}

export function isTokenExpired(): boolean {
  const payload = getDecodedToken();
  if (!payload) return true;
  return Date.now() / 1000 > payload.exp;
}
