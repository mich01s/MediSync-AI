/**
 * MediSync AI — Patient: Encounters History Page
 * Displays full encounter history with vitals and treatment plan details.
 */
"use client";

import { useEffect, useState } from "react";
import { Activity, ChevronDown, ChevronUp } from "lucide-react";
import toast from "react-hot-toast";
import { patientApi } from "@/lib/api";
import { type Encounter, type TreatmentPlan } from "@/types";
import { Sidebar } from "@/components/ui/Sidebar";
import {
  LoadingSpinner,
  EmptyState,
  SectionHeader,
  Badge,
  EWSBadge,
} from "@/components/ui";
import { format, parseISO } from "date-fns";
import { apiClient } from "@/lib/api";

export default function PatientEncountersPage() {
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [plans, setPlans] = useState<Map<string, TreatmentPlan>>(new Map());
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    patientApi
      .getMyEncounters()
      .then(async (encs: Encounter[]) => {
        setEncounters(encs);
        // Lazily fetch treatment plans for each encounter
        const planMap = new Map<string, TreatmentPlan>();
        await Promise.all(
          encs.map(async (enc) => {
            try {
              const { data } = await apiClient.get<TreatmentPlan>(
                `/patient/encounters/${enc.id}/treatment-plan`
              );
              planMap.set(enc.id, data);
            } catch {
              // No plan yet
            }
          })
        );
        setPlans(planMap);
      })
      .catch(() => toast.error("Failed to load encounter history."))
      .finally(() => setLoading(false));
  }, []);

  const toggle = (id: string) =>
    setExpanded((prev) => (prev === id ? null : id));

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">My Health History</h1>
          <p className="text-sm text-slate-500 mt-1">
            All your past consultations and examination records
          </p>
        </div>

        <div className="card p-5">
          <SectionHeader
            title="Consultation History"
            subtitle={`${encounters.length} visits`}
          />

          {loading ? (
            <div className="flex justify-center py-16">
              <LoadingSpinner />
            </div>
          ) : encounters.length === 0 ? (
            <EmptyState
              icon={Activity}
              title="No visits yet"
              description="Your consultation history will appear here after your first visit."
            />
          ) : (
            <div className="space-y-2">
              {encounters.map((enc) => {
                const plan = plans.get(enc.id);
                return (
                  <div
                    key={enc.id}
                    className="rounded-xl border border-slate-200 overflow-hidden"
                  >
                    {/* Row header */}
                    <button
                      className="w-full flex items-center gap-3 p-4 hover:bg-slate-50 text-left transition-colors"
                      onClick={() => toggle(enc.id)}
                    >
                      <Activity size={16} className="text-primary-500 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-800 line-clamp-1">
                          {enc.complaint_text ?? "Consultation recorded"}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {format(parseISO(enc.created_at), "PPPP")}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {plan && <EWSBadge level={plan.ews_level} />}
                        {expanded === enc.id ? (
                          <ChevronUp size={16} className="text-slate-400" />
                        ) : (
                          <ChevronDown size={16} className="text-slate-400" />
                        )}
                      </div>
                    </button>

                    {/* Expanded details */}
                    {expanded === enc.id && (
                      <div className="border-t border-slate-100 bg-slate-50 p-5 space-y-5">
                        {/* Vitals */}
                        {enc.tabular_metrics_json &&
                          Object.keys(enc.tabular_metrics_json).length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-slate-500 uppercase mb-2">
                                Recorded Vital Signs
                              </p>
                              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                {Object.entries(enc.tabular_metrics_json).map(
                                  ([k, v]) => (
                                    <div
                                      key={k}
                                      className="bg-white rounded-lg px-3 py-2.5 border border-slate-200"
                                    >
                                      <p className="text-xs text-slate-400 capitalize mb-0.5">
                                        {k.replace(/_/g, " ")}
                                      </p>
                                      <p className="font-mono font-bold text-slate-900">
                                        {v}
                                      </p>
                                    </div>
                                  )
                                )}
                              </div>
                            </div>
                          )}

                        {/* Treatment Plan */}
                        {plan ? (
                          <div>
                            <p className="text-xs font-semibold text-slate-500 uppercase mb-2">
                              Treatment Plan
                            </p>
                            <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-3">
                              {plan.diagnosis && (
                                <div>
                                  <p className="text-xs text-slate-400 mb-0.5">Diagnosis</p>
                                  <p className="text-sm font-medium text-slate-800">
                                    {plan.diagnosis}
                                  </p>
                                </div>
                              )}
                              {plan.prescription_drugs &&
                                plan.prescription_drugs.length > 0 && (
                                  <div>
                                    <p className="text-xs text-slate-400 mb-1.5">
                                      Medications
                                    </p>
                                    <div className="space-y-1.5">
                                      {plan.prescription_drugs.map((drug, i) => (
                                        <div
                                          key={i}
                                          className="flex gap-2 text-sm text-slate-700"
                                        >
                                          <span className="font-medium">
                                            {String(
                                              (drug as Record<string, unknown>)
                                                .drug ?? drug
                                            )}
                                          </span>
                                          {(drug as Record<string, unknown>)
                                            .dose && (
                                            <span className="text-slate-400">
                                              {String(
                                                (drug as Record<string, unknown>)
                                                  .dose
                                              )}{" "}
                                              ·{" "}
                                              {String(
                                                (drug as Record<string, unknown>)
                                                  .frequency ?? ""
                                              )}
                                            </span>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              {plan.behavioral_advice && (
                                <div>
                                  <p className="text-xs text-slate-400 mb-0.5">
                                    Lifestyle Advice
                                  </p>
                                  <p className="text-sm text-slate-700 leading-relaxed">
                                    {plan.behavioral_advice}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        ) : (
                          <p className="text-sm text-slate-400">
                            No treatment plan on record for this visit.
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
