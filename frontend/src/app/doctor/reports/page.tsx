/**
 * MediSync AI — Doctor Reports Page
 * Doctors review encounter reports, approve drafts, and view approved reports.
 */
"use client";

import { useEffect, useState } from "react";
import { FileText, CheckCircle, XCircle } from "lucide-react";
import toast from "react-hot-toast";
import { doctorApi } from "@/lib/api";
import { type Encounter, type ClinicalReport } from "@/types";
import {
  LoadingSpinner,
  SectionHeader,
  EmptyState,
  Badge,
} from "@/components/ui";
import { Sidebar } from "@/components/ui/Sidebar";
import { format } from "date-fns";
import { apiClient } from "@/lib/api";

export default function DoctorReportsPage() {
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [reports, setReports] = useState<Map<string, ClinicalReport>>(new Map());
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<ClinicalReport | null>(null);

  useEffect(() => {
    doctorApi
      .getMyEncounters()
      .then(async (encs: Encounter[]) => {
        setEncounters(encs);
        // Fetch reports for each encounter that has one
        const rMap = new Map<string, ClinicalReport>();
        await Promise.all(
          encs.map(async (enc) => {
            try {
              const { data } = await apiClient.get<ClinicalReport>(
                `/doctor/encounters/${enc.id}/generate-report`
              );
              rMap.set(enc.id, data);
            } catch {
              // No report yet — skip
            }
          })
        );
        setReports(rMap);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleApprove = async (reportId: string, approve: boolean) => {
    try {
      const updated = await doctorApi.approveReport(reportId, approve);
      setReports((prev) => {
        const next = new Map(prev);
        // Update in map
        next.forEach((v, k) => {
          if (v.id === reportId) next.set(k, updated);
        });
        return next;
      });
      if (selected?.id === reportId) setSelected(updated);
      toast.success(approve ? "Report approved!" : "Report returned to draft.");
    } catch {
      toast.error("Failed to update report status.");
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">Clinical Reports</h1>
          <p className="text-sm text-slate-500 mt-1">
            Review and approve LLM-generated patient reports
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-24">
            <LoadingSpinner size={36} />
          </div>
        ) : (
          <div className="grid lg:grid-cols-5 gap-6">
            {/* Report List */}
            <div className="lg:col-span-2 card p-5">
              <SectionHeader title="Encounters with Reports" />
              {encounters.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="No encounters"
                  description="Reports will appear here once encounters are recorded."
                />
              ) : (
                <div className="space-y-2">
                  {encounters.map((enc) => {
                    const report = reports.get(enc.id);
                    return (
                      <button
                        key={enc.id}
                        className={`w-full text-left p-3 rounded-lg border transition-all ${
                          selected?.encounter_id === enc.id
                            ? "border-primary-400 bg-primary-50"
                            : "border-slate-200 hover:border-slate-300"
                        }`}
                        onClick={() => report && setSelected(report)}
                      >
                        <p className="text-sm font-medium text-slate-800 line-clamp-1">
                          {enc.complaint_text ?? enc.id.slice(0, 12) + "…"}
                        </p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span className="text-xs text-slate-400">
                            {format(new Date(enc.created_at), "MMM d, yyyy")}
                          </span>
                          {report ? (
                            <Badge
                              variant={
                                report.status === "approved" ? "green" : "yellow"
                              }
                            >
                              {report.status}
                            </Badge>
                          ) : (
                            <Badge variant="gray">No report</Badge>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Report Detail */}
            <div className="lg:col-span-3 card p-5">
              {selected ? (
                <>
                  <div className="flex items-start justify-between mb-4 gap-3">
                    <div>
                      <h3 className="font-bold text-slate-900">Report Preview</h3>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {format(new Date(selected.created_at), "PPPp")}
                      </p>
                    </div>
                    <Badge
                      variant={selected.status === "approved" ? "green" : "yellow"}
                    >
                      {selected.status}
                    </Badge>
                  </div>

                  <div className="bg-slate-50 rounded-xl p-4 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto mb-4">
                    {selected.patient_friendly_report ?? "No content yet."}
                  </div>

                  {/* Approve / Reject Buttons */}
                  {selected.status === "draft" && (
                    <div className="flex gap-3">
                      <button
                        className="btn-primary"
                        onClick={() => handleApprove(selected.id, true)}
                      >
                        <CheckCircle size={16} />
                        Approve & Publish
                      </button>
                      <button
                        className="btn-secondary text-red-600 border-red-200 hover:bg-red-50"
                        onClick={() => handleApprove(selected.id, false)}
                      >
                        <XCircle size={16} />
                        Request Revision
                      </button>
                    </div>
                  )}
                  {selected.status === "approved" && (
                    <p className="text-sm text-green-600 font-medium flex items-center gap-1.5">
                      <CheckCircle size={15} />
                      This report is published and visible to the patient.
                    </p>
                  )}
                </>
              ) : (
                <EmptyState
                  icon={FileText}
                  title="Select a report"
                  description="Click on an encounter with a report to preview it here."
                />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
