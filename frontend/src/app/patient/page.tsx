/**
 * MediSync AI — Patient Dashboard
 * Shows queue status, encounter history, and approved health reports.
 */
"use client";

import { useEffect, useState } from "react";
import {
  ClipboardList,
  Activity,
  FileText,
  CheckCircle2,
  Clock,
  UserCircle,
} from "lucide-react";
import { patientApi } from "@/lib/api";
import { type Queue, type Encounter, type ClinicalReport } from "@/types";
import {
  LoadingSpinner,
  SectionHeader,
  EmptyState,
  QueueStatusBadge,
  EWSBadge,
} from "@/components/ui";
import { Sidebar } from "@/components/ui/Sidebar";
import { format } from "date-fns";

export default function PatientDashboard() {
  const [queues, setQueues] = useState<Queue[]>([]);
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [reports, setReports] = useState<ClinicalReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<ClinicalReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      patientApi.getMyQueue(),
      patientApi.getMyEncounters(),
      patientApi.getMyReports(),
    ])
      .then(([q, e, r]) => {
        setQueues(q);
        setEncounters(e);
        setReports(r);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8 max-w-5xl">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900">My Health Portal</h1>
          <p className="text-sm text-slate-500 mt-1">
            Queue status, visit history, and health reports
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-24">
            <LoadingSpinner size={36} />
          </div>
        ) : selectedReport ? (
          // ── Report Detail View ────────────────────────────────────────────
          <div className="card p-6 max-w-2xl">
            <button
              className="text-sm text-primary-600 hover:underline mb-4 flex items-center gap-1"
              onClick={() => setSelectedReport(null)}
            >
              ← Back to dashboard
            </button>
            <h2 className="text-lg font-bold text-slate-900 mb-1">
              Health Summary Report
            </h2>
            <p className="text-xs text-slate-400 mb-5">
              {format(new Date(selectedReport.created_at), "PPP")}
            </p>
            <div className="prose prose-sm max-w-none text-slate-700 whitespace-pre-wrap leading-relaxed">
              {selectedReport.patient_friendly_report ?? "Report content unavailable."}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* ── Queue Status ──────────────────────────────────────────── */}
            <div className="card p-5">
              <SectionHeader
                title="My Current Queue"
                subtitle="Real-time status"
              />
              {queues.length === 0 ? (
                <EmptyState
                  icon={ClipboardList}
                  title="No active queue"
                  description="You are not currently registered in any queue."
                />
              ) : (
                <div className="grid sm:grid-cols-2 gap-3">
                  {queues.map((q) => (
                    <div
                      key={q.id}
                      className={`p-4 rounded-xl border-2 ${
                        q.status === "serving"
                          ? "border-primary-400 bg-primary-50"
                          : "border-slate-200 bg-white"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-slate-500 uppercase">
                          {q.poli_name}
                        </span>
                        <QueueStatusBadge status={q.status} />
                      </div>
                      <p className="text-5xl font-black text-primary-600 font-mono text-center py-3">
                        {String(q.queue_number).padStart(3, "0")}
                      </p>
                      {q.status === "serving" && (
                        <p className="text-center text-sm text-primary-700 font-medium">
                          🏥 It&apos;s your turn — please proceed to the room
                        </p>
                      )}
                      {q.status === "waiting" && (
                        <p className="text-center text-xs text-slate-400 mt-1 flex items-center justify-center gap-1">
                          <Clock size={12} />
                          Waiting
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* ── Encounter History ────────────────────────────────────── */}
            <div className="card p-5">
              <SectionHeader
                title="Visit History"
                subtitle={`${encounters.length} encounters`}
              />
              {encounters.length === 0 ? (
                <EmptyState
                  icon={Activity}
                  title="No visits yet"
                  description="Your consultation history will appear here."
                />
              ) : (
                <div className="space-y-2">
                  {encounters.slice(0, 5).map((enc) => (
                    <div
                      key={enc.id}
                      className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50"
                    >
                      <Activity size={16} className="text-slate-400 mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm text-slate-700 line-clamp-1">
                          {enc.complaint_text ?? "Encounter recorded"}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {format(new Date(enc.created_at), "PPP")}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* ── My Reports ───────────────────────────────────────────── */}
            <div className="card p-5">
              <SectionHeader
                title="My Health Reports"
                subtitle="Doctor-approved reports"
              />
              {reports.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="No reports yet"
                  description="Approved medical reports from your doctor will appear here."
                />
              ) : (
                <div className="space-y-2">
                  {reports.map((r) => (
                    <button
                      key={r.id}
                      className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-primary-50 text-left transition-colors group"
                      onClick={() => setSelectedReport(r)}
                    >
                      <CheckCircle2 size={16} className="text-green-500 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-800 line-clamp-1 group-hover:text-primary-700">
                          Health Report —{" "}
                          {format(new Date(r.created_at), "PPP")}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Click to read your personalised summary
                        </p>
                      </div>
                      <span className="ml-auto text-xs text-primary-600 font-medium shrink-0">
                        Read →
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
