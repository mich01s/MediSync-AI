/**
 * MediSync AI — Doctor: AI Insights Page
 * Run multi-modal AI analysis on any encounter and inspect results.
 */
"use client";

import { useEffect, useState } from "react";
import { Zap, Activity } from "lucide-react";
import toast from "react-hot-toast";
import { doctorApi } from "@/lib/api";
import { type Encounter, type AIPrediction } from "@/types";
import { Sidebar } from "@/components/ui/Sidebar";
import {
  LoadingSpinner,
  EmptyState,
  SectionHeader,
  Badge,
} from "@/components/ui";
import { AIInsightsPanel } from "@/components/ai-insights/AIInsightsPanel";

export default function DoctorAIPage() {
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Encounter | null>(null);
  const [predictions, setPredictions] = useState<AIPrediction[]>([]);
  const [predicting, setPredicting] = useState(false);

  // Options for which modalities to run
  const [runTabular, setRunTabular] = useState(true);
  const [runNlp, setRunNlp] = useState(true);
  const [runVision, setRunVision] = useState(false);

  useEffect(() => {
    doctorApi
      .getMyEncounters()
      .then(setEncounters)
      .catch(() => toast.error("Failed to load encounters."))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectEncounter = (enc: Encounter) => {
    setSelected(enc);
    setPredictions([]);
    // Auto-toggle modalities based on what data exists
    setRunTabular(!!enc.tabular_metrics_json);
    setRunNlp(!!enc.complaint_text);
    setRunVision(!!enc.medical_image_key);
  };

  const handleRunAI = async () => {
    if (!selected) return;
    setPredicting(true);
    try {
      const results = await doctorApi.runPrediction({
        encounter_id: selected.id,
        run_tabular: runTabular,
        run_nlp: runNlp,
        run_vision: runVision,
      });
      setPredictions(results);
      toast.success(`${results.length} AI model(s) completed analysis.`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "AI prediction failed.";
      toast.error(msg);
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">AI Insights</h1>
          <p className="text-sm text-slate-500 mt-1">
            Multi-modal AI analysis: vital signs, NLP complaint, medical imaging
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-24">
            <LoadingSpinner size={36} />
          </div>
        ) : (
          <div className="grid lg:grid-cols-5 gap-6">
            {/* Left: Encounter selector */}
            <div className="lg:col-span-2 space-y-4">
              <div className="card p-5">
                <SectionHeader
                  title="Select Encounter"
                  subtitle="Choose an encounter to analyse"
                />
                {encounters.length === 0 ? (
                  <EmptyState
                    icon={Activity}
                    title="No encounters"
                    description="Encounters will appear here once created."
                  />
                ) : (
                  <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1">
                    {encounters.map((enc) => (
                      <button
                        key={enc.id}
                        className={`w-full text-left p-3 rounded-xl border transition-all ${
                          selected?.id === enc.id
                            ? "border-primary-400 bg-primary-50"
                            : "border-slate-200 hover:border-slate-300 bg-white"
                        }`}
                        onClick={() => handleSelectEncounter(enc)}
                      >
                        <p className="text-sm font-medium text-slate-800 line-clamp-1">
                          {enc.complaint_text ?? "No complaint recorded"}
                        </p>
                        <div className="flex gap-1.5 mt-1.5 flex-wrap">
                          {enc.tabular_metrics_json && (
                            <Badge variant="blue">Vitals</Badge>
                          )}
                          {enc.complaint_text && (
                            <Badge variant="purple">Text</Badge>
                          )}
                          {enc.medical_image_key && (
                            <Badge variant="green">Image</Badge>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Modality toggles */}
              {selected && (
                <div className="card p-5">
                  <p className="text-sm font-semibold text-slate-700 mb-3">
                    Active Modalities
                  </p>
                  <div className="space-y-2">
                    {[
                      {
                        key: "tabular",
                        label: "Vital Signs (XGBoost)",
                        enabled: runTabular,
                        set: setRunTabular,
                        available: !!selected.tabular_metrics_json,
                      },
                      {
                        key: "nlp",
                        label: "Complaint NLP",
                        enabled: runNlp,
                        set: setRunNlp,
                        available: !!selected.complaint_text,
                      },
                      {
                        key: "vision",
                        label: "Medical Imaging",
                        enabled: runVision,
                        set: setRunVision,
                        available: !!selected.medical_image_key,
                      },
                    ].map(({ key, label, enabled, set, available }) => (
                      <label
                        key={key}
                        className={`flex items-center gap-3 p-2.5 rounded-lg cursor-pointer transition-colors ${
                          available ? "hover:bg-slate-50" : "opacity-40 cursor-not-allowed"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={enabled && available}
                          disabled={!available}
                          onChange={(e) => set(e.target.checked)}
                          className="w-4 h-4 accent-primary-600"
                        />
                        <span className="text-sm text-slate-700">{label}</span>
                        {!available && (
                          <span className="text-xs text-slate-400 ml-auto">
                            No data
                          </span>
                        )}
                      </label>
                    ))}
                  </div>

                  <button
                    className="btn-primary w-full justify-center mt-4"
                    onClick={handleRunAI}
                    disabled={
                      predicting ||
                      (!runTabular && !runNlp && !runVision) ||
                      !(
                        (runTabular && !!selected.tabular_metrics_json) ||
                        (runNlp && !!selected.complaint_text) ||
                        (runVision && !!selected.medical_image_key)
                      )
                    }
                  >
                    <Zap size={16} />
                    {predicting ? "Analysing…" : "Run AI Analysis"}
                  </button>
                </div>
              )}
            </div>

            {/* Right: Results */}
            <div className="lg:col-span-3 card p-5">
              {predicting ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4">
                  <LoadingSpinner size={36} />
                  <p className="text-sm text-slate-500 font-medium">
                    Running AI pipeline…
                  </p>
                  <p className="text-xs text-slate-400">
                    Processing selected modalities
                  </p>
                </div>
              ) : predictions.length > 0 ? (
                <AIInsightsPanel predictions={predictions} />
              ) : selected ? (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                  <Zap size={40} className="text-slate-200 mb-4" />
                  <p className="text-sm font-medium text-slate-600">
                    Ready to analyse
                  </p>
                  <p className="text-xs text-slate-400 mt-1 max-w-xs">
                    Select modalities and click &quot;Run AI Analysis&quot; to see
                    multi-modal prediction results.
                  </p>
                </div>
              ) : (
                <EmptyState
                  icon={Zap}
                  title="No encounter selected"
                  description="Select an encounter on the left to start AI analysis."
                />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
