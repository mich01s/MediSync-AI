/**
 * MediSync AI — Doctor Dashboard
 * Shows encounter list, quick AI prediction trigger, and EWS status.
 */
"use client";

import { useEffect, useState } from "react";
import { Activity, Plus, Zap, FileText } from "lucide-react";
import toast from "react-hot-toast";
import { doctorApi } from "@/lib/api";
import { type Encounter, type AIPrediction } from "@/types";
import {
  LoadingSpinner,
  SectionHeader,
  EmptyState,
  EWSBadge,
  Badge,
} from "@/components/ui";
import { AIInsightsPanel } from "@/components/ai-insights/AIInsightsPanel";
import { Sidebar } from "@/components/ui/Sidebar";

export default function DoctorDashboard() {
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Encounter | null>(null);
  const [predictions, setPredictions] = useState<AIPrediction[]>([]);
  const [predicting, setPredicting] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    doctorApi
      .getMyEncounters()
      .then(setEncounters)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleRunAI = async (enc: Encounter) => {
    setPredicting(true);
    try {
      const results = await doctorApi.runPrediction({
        encounter_id: enc.id,
        run_tabular: !!enc.tabular_metrics_json,
        run_nlp: !!enc.complaint_text,
        run_vision: !!enc.medical_image_key,
      });
      setPredictions(results);
      setSelected(enc);
      toast.success("AI analysis complete!");
    } catch {
      toast.error("AI prediction failed.");
    } finally {
      setPredicting(false);
    }
  };

  const handleGenerateReport = async (enc: Encounter) => {
    setGenerating(true);
    try {
      await doctorApi.generateReport(enc.id);
      toast.success("Report draft generated!");
    } catch {
      toast.error("Report generation failed.");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900">Doctor Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage encounters and AI-assisted diagnostics
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-24">
            <LoadingSpinner size={36} />
          </div>
        ) : (
          <div className="grid lg:grid-cols-5 gap-6">
            {/* Encounter List — 3 cols */}
            <div className="lg:col-span-3 card p-5">
              <SectionHeader
                title="My Encounters"
                subtitle={`${encounters.length} total`}
              />

              {encounters.length === 0 ? (
                <EmptyState
                  icon={Activity}
                  title="No encounters yet"
                  description="Encounters created by admin will appear here."
                />
              ) : (
                <div className="space-y-3">
                  {encounters.map((enc) => (
                    <div
                      key={enc.id}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${
                        selected?.id === enc.id
                          ? "border-primary-400 bg-primary-50"
                          : "border-slate-200 bg-white hover:border-slate-300"
                      }`}
                      onClick={() => {
                        setSelected(enc);
                        setPredictions([]);
                      }}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="font-mono text-xs text-slate-400">
                            {enc.id.slice(0, 12)}…
                          </p>
                          <p className="text-sm font-medium text-slate-800 mt-1 line-clamp-2">
                            {enc.complaint_text ?? "No complaint recorded"}
                          </p>
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            <Badge
                              variant={
                                enc.status === "open"
                                  ? "blue"
                                  : enc.status === "closed"
                                  ? "green"
                                  : "yellow"
                              }
                            >
                              {enc.status}
                            </Badge>
                            {enc.tabular_metrics_json && (
                              <Badge variant="gray">Vitals</Badge>
                            )}
                            {enc.medical_image_key && (
                              <Badge variant="purple">Image</Badge>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-2 shrink-0">
                          <button
                            className="btn-secondary text-xs px-2 py-1.5"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRunAI(enc);
                            }}
                            disabled={predicting}
                          >
                            <Zap size={13} />
                            {predicting ? "…" : "AI"}
                          </button>
                          <button
                            className="btn-secondary text-xs px-2 py-1.5"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleGenerateReport(enc);
                            }}
                            disabled={generating}
                          >
                            <FileText size={13} />
                            {generating ? "…" : "Report"}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* AI Panel — 2 cols */}
            <div className="lg:col-span-2 card p-5">
              {predicting ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                  <LoadingSpinner size={32} />
                  <p className="text-sm text-slate-500">Running AI analysis…</p>
                </div>
              ) : (
                <AIInsightsPanel predictions={predictions} />
              )}

              {selected && predictions.length === 0 && !predicting && (
                <div className="text-center py-8">
                  <p className="text-sm text-slate-400">
                    Click <strong>AI</strong> on an encounter to run multi-modal prediction.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
