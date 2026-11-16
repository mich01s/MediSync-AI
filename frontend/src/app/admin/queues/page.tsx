/**
 * MediSync AI — Admin Queue Monitor Page
 * Full real-time view of all polis with filtering.
 */
"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { adminApi, queueApi } from "@/lib/api";
import { type Queue } from "@/types";
import {
  LoadingSpinner,
  SectionHeader,
  QueueStatusBadge,
} from "@/components/ui";
import { QueueBoard } from "@/components/queue-board/QueueBoard";
import { Sidebar } from "@/components/ui/Sidebar";
import toast from "react-hot-toast";

const POLIS = ["General", "Cardiology", "Pediatrics", "Orthopedics", "Neurology"];

export default function AdminQueuesPage() {
  const [queues, setQueues] = useState<Queue[]>([]);
  const [loading, setLoading] = useState(true);
  const [activePoli, setActivePoli] = useState("General");

  const fetchQueues = async () => {
    setLoading(true);
    try {
      const data = await adminApi.listQueues();
      setQueues(data);
    } catch {
      toast.error("Failed to load queues.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueues();
  }, []);

  const updateStatus = async (queueId: string, status: string) => {
    try {
      await queueApi.updateStatus(queueId, status);
      toast.success(`Queue status updated to ${status}`);
      fetchQueues();
    } catch {
      toast.error("Failed to update status.");
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Queue Monitor</h1>
            <p className="text-sm text-slate-500 mt-1">
              Real-time queue management across all polis
            </p>
          </div>
          <button className="btn-secondary" onClick={fetchQueues}>
            <RefreshCw size={15} />
            Refresh
          </button>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Live Board */}
          <div className="lg:col-span-1 card p-5">
            <SectionHeader title="Live Board" />
            {/* Poli Tabs */}
            <div className="flex flex-wrap gap-1.5 mb-4">
              {POLIS.map((p) => (
                <button
                  key={p}
                  onClick={() => setActivePoli(p)}
                  className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${
                    activePoli === p
                      ? "bg-primary-600 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
            <QueueBoard poliName={activePoli} compact />
          </div>

          {/* All Queues Table */}
          <div className="lg:col-span-2 card p-5">
            <SectionHeader
              title="All Queue Entries"
              subtitle={`${queues.length} total`}
            />
            {loading ? (
              <div className="flex justify-center py-16">
                <LoadingSpinner />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200">
                      {["Queue #", "Poli", "Patient", "Status", "Actions"].map(
                        (h) => (
                          <th
                            key={h}
                            className="text-left py-2 px-3 text-xs font-semibold text-slate-400 uppercase"
                          >
                            {h}
                          </th>
                        )
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {queues.map((q) => (
                      <tr
                        key={q.id}
                        className="border-b border-slate-100 last:border-0 hover:bg-slate-50"
                      >
                        <td className="py-2.5 px-3 font-mono font-bold text-primary-600">
                          #{String(q.queue_number).padStart(3, "0")}
                        </td>
                        <td className="py-2.5 px-3 text-slate-700">{q.poli_name}</td>
                        <td className="py-2.5 px-3 font-mono text-xs text-slate-500">
                          {q.patient_id.slice(0, 8)}…
                        </td>
                        <td className="py-2.5 px-3">
                          <QueueStatusBadge status={q.status} />
                        </td>
                        <td className="py-2.5 px-3">
                          {q.status === "waiting" && (
                            <button
                              className="text-xs text-primary-600 hover:underline"
                              onClick={() => updateStatus(q.id, "serving")}
                            >
                              Call
                            </button>
                          )}
                          {q.status === "serving" && (
                            <button
                              className="text-xs text-green-600 hover:underline"
                              onClick={() => updateStatus(q.id, "done")}
                            >
                              Done
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                    {queues.length === 0 && (
                      <tr>
                        <td
                          colSpan={5}
                          className="py-10 text-center text-slate-400 text-sm"
                        >
                          No queue entries found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
