/**
 * MediSync AI — Queue Board Component
 * Displays live queue entries for a poli with WebSocket updates.
 */
"use client";

import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import { QueueWebSocket } from "@/lib/websocket";
import { queueApi } from "@/lib/api";
import { type Queue } from "@/types";
import { QueueStatusBadge, LoadingSpinner, EmptyState } from "@/components/ui";

interface QueueBoardProps {
  poliName: string;
  /** If true, renders compact rows instead of large numbered cards. */
  compact?: boolean;
}

export function QueueBoard({ poliName, compact = false }: QueueBoardProps) {
  const [entries, setEntries] = useState<Queue[]>([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  // Load initial queue state
  useEffect(() => {
    queueApi
      .getPoliQueue(poliName)
      .then(setEntries)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [poliName]);

  // Subscribe to real-time updates
  useEffect(() => {
    const ws = new QueueWebSocket(poliName);

    ws.onConnect = () => setConnected(true);
    ws.onDisconnect = () => setConnected(false);
    ws.onUpdate = (update: Queue) => {
      setEntries((prev) => {
        const idx = prev.findIndex((e) => e.id === update.id);
        if (idx === -1) return [...prev, update];
        const next = [...prev];
        next[idx] = update;
        return next.filter((e) => e.status !== "done" && e.status !== "cancelled");
      });
    };

    ws.connect();
    return () => ws.disconnect();
  }, [poliName]);

  if (loading) {
    return (
      <div className="flex justify-center py-10">
        <LoadingSpinner />
      </div>
    );
  }

  const active = entries.filter(
    (e) => e.status === "waiting" || e.status === "serving"
  );

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-800">
          Poli: <span className="text-primary-600">{poliName}</span>
        </h3>
        <span
          className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full
            ${connected ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-green-500" : "bg-slate-400"}`}
          />
          {connected ? "Live" : "Offline"}
        </span>
      </div>

      {active.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No active queue"
          description="Queue is currently empty for this poli."
        />
      ) : compact ? (
        // Compact table view (admin/doctor)
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase">
                  No.
                </th>
                <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase">
                  Patient ID
                </th>
                <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {active.map((entry) => (
                <tr key={entry.id} className="border-b border-slate-100 last:border-0">
                  <td className="py-2.5 px-3 font-mono font-bold text-primary-600">
                    #{String(entry.queue_number).padStart(3, "0")}
                  </td>
                  <td className="py-2.5 px-3 text-slate-600 font-mono text-xs">
                    {entry.patient_id.slice(0, 8)}…
                  </td>
                  <td className="py-2.5 px-3">
                    <QueueStatusBadge status={entry.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        // Large card view (patient-facing display board)
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {active.map((entry) => (
            <div
              key={entry.id}
              className={`rounded-xl p-4 border-2 text-center transition-all ${
                entry.status === "serving"
                  ? "border-primary-500 bg-primary-50"
                  : "border-slate-200 bg-white"
              }`}
            >
              <p className="text-4xl font-black text-primary-600 font-mono">
                {String(entry.queue_number).padStart(3, "0")}
              </p>
              <QueueStatusBadge status={entry.status} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
