/**
 * MediSync AI — Reusable UI Components
 * StatCard, Badge, EWSBadge, LoadingSpinner, EmptyState
 */
"use client";

import { type ReactNode } from "react";
import { clsx } from "clsx";
import { type LucideIcon } from "lucide-react";

// ── StatCard ──────────────────────────────────────────────────────────────────

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  iconColor?: string;
  delta?: string;
  deltaPositive?: boolean;
}

export function StatCard({
  title,
  value,
  icon: Icon,
  iconColor = "text-primary-600",
  delta,
  deltaPositive,
}: StatCardProps) {
  return (
    <div className="card p-5 flex items-start gap-4">
      <div className={clsx("p-2.5 rounded-lg bg-slate-100", iconColor)}>
        <Icon size={22} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-500 font-medium truncate">{title}</p>
        <p className="text-2xl font-bold text-slate-900 mt-0.5">{value}</p>
        {delta && (
          <p
            className={clsx(
              "text-xs mt-1 font-medium",
              deltaPositive ? "text-green-600" : "text-red-500"
            )}
          >
            {delta}
          </p>
        )}
      </div>
    </div>
  );
}

// ── Badge ─────────────────────────────────────────────────────────────────────

type BadgeVariant = "green" | "blue" | "yellow" | "red" | "gray" | "purple";

export function Badge({
  children,
  variant = "gray",
}: {
  children: ReactNode;
  variant?: BadgeVariant;
}) {
  const styles: Record<BadgeVariant, string> = {
    green: "bg-green-100 text-green-700",
    blue: "bg-blue-100 text-blue-700",
    yellow: "bg-yellow-100 text-yellow-700",
    red: "bg-red-100 text-red-700",
    gray: "bg-slate-100 text-slate-600",
    purple: "bg-purple-100 text-purple-700",
  };
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        styles[variant]
      )}
    >
      {children}
    </span>
  );
}

// ── EWSBadge ──────────────────────────────────────────────────────────────────

const EWS_CONFIG = [
  { label: "Normal", class: "bg-green-100 text-green-700" },
  { label: "Low Risk", class: "bg-yellow-100 text-yellow-700" },
  { label: "Medium Risk", class: "bg-orange-100 text-orange-700" },
  { label: "CRITICAL", class: "bg-red-100 text-red-700 animate-pulse font-bold" },
];

export function EWSBadge({ level }: { level: number }) {
  const config = EWS_CONFIG[Math.min(level, 3)];
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs",
        config.class
      )}
    >
      EWS {level} — {config.label}
    </span>
  );
}

// ── QueueStatusBadge ──────────────────────────────────────────────────────────

const QUEUE_STATUS_STYLES: Record<string, BadgeVariant> = {
  waiting: "yellow",
  serving: "blue",
  done: "green",
  cancelled: "gray",
};

export function QueueStatusBadge({ status }: { status: string }) {
  return (
    <Badge variant={QUEUE_STATUS_STYLES[status] ?? "gray"}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}

// ── LoadingSpinner ────────────────────────────────────────────────────────────

export function LoadingSpinner({ size = 24 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className="animate-spin text-primary-600"
      aria-label="Loading"
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="3"
        strokeDasharray="40 60"
        strokeLinecap="round"
      />
    </svg>
  );
}

// ── EmptyState ────────────────────────────────────────────────────────────────

export function EmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Icon size={48} className="text-slate-300 mb-4" />
      <h3 className="text-base font-semibold text-slate-700">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-slate-400 max-w-xs">{description}</p>
      )}
    </div>
  );
}

// ── SectionHeader ─────────────────────────────────────────────────────────────

export function SectionHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between mb-5">
      <div>
        <h2 className="text-lg font-bold text-slate-900">{title}</h2>
        {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
