/**
 * MediSync AI — AI Insights Panel
 * Renders multi-modal prediction results with per-modality breakdowns.
 */
"use client";

import { type AIPrediction } from "@/types";
import { Zap, FileText, Eye, BarChart2 } from "lucide-react";
import { Badge } from "@/components/ui";

interface AIInsightsPanelProps {
  predictions: AIPrediction[];
}

const MODEL_META: Record<
  string,
  { label: string; icon: React.ElementType; color: string }
> = {
  tabular_xgboost: { label: "Vital Signs Risk", icon: BarChart2, color: "blue" },
  nlp_extractor: { label: "Complaint NLP", icon: FileText, color: "purple" },
  vision_cnn: { label: "Medical Imaging", icon: Eye, color: "green" },
};

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80 ? "bg-green-500" : pct >= 60 ? "bg-yellow-500" : "bg-red-400";
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 bg-slate-100 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-600 w-10 text-right">{pct}%</span>
    </div>
  );
}

function PredictionCard({ prediction }: { prediction: AIPrediction }) {
  const meta = MODEL_META[prediction.model_name] ?? {
    label: prediction.model_name,
    icon: Zap,
    color: "gray",
  };
  const result = prediction.prediction_result_json as Record<string, unknown>;

  return (
    <div className="card p-4">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-3">
        <meta.icon size={18} className="text-primary-600" />
        <span className="font-semibold text-sm text-slate-800">{meta.label}</span>
        <span className="ml-auto">
          <Badge variant={meta.color as "blue" | "purple" | "green" | "gray"}>
            {String(result.mode ?? "AI")}
          </Badge>
        </span>
      </div>

      {/* Confidence */}
      {prediction.confidence_score !== null && (
        <div className="mb-3">
          <p className="text-xs text-slate-500">Confidence</p>
          <ConfidenceBar score={prediction.confidence_score} />
        </div>
      )}

      {/* Key result */}
      {result.predicted_label && (
        <div className="mt-2 p-2.5 bg-slate-50 rounded-lg">
          <p className="text-xs text-slate-500 mb-0.5">Predicted Risk</p>
          <p className="font-bold text-slate-900 capitalize">
            {String(result.predicted_label).replace(/_/g, " ")}
          </p>
        </div>
      )}

      {result.predicted_finding && (
        <div className="mt-2 p-2.5 bg-slate-50 rounded-lg">
          <p className="text-xs text-slate-500 mb-0.5">Imaging Finding</p>
          <p className="font-bold text-slate-900 capitalize">
            {String(result.predicted_finding).replace(/_/g, " ")}
          </p>
        </div>
      )}

      {result.matched_symptoms && Array.isArray(result.matched_symptoms) && (
        <div className="mt-2">
          <p className="text-xs text-slate-500 mb-1.5">Detected Symptoms</p>
          <div className="flex flex-wrap gap-1.5">
            {(result.matched_symptoms as string[]).map((sym) => (
              <Badge key={sym} variant="yellow">
                {sym}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {result.candidate_diagnoses && Array.isArray(result.candidate_diagnoses) && (
        <div className="mt-2">
          <p className="text-xs text-slate-500 mb-1.5">Candidate Diagnoses</p>
          <div className="flex flex-wrap gap-1.5">
            {(result.candidate_diagnoses as string[]).slice(0, 5).map((dx) => (
              <Badge key={dx} variant="blue">
                {dx.replace(/_/g, " ")}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function AIInsightsPanel({ predictions }: AIInsightsPanelProps) {
  if (predictions.length === 0) {
    return (
      <div className="text-sm text-slate-400 text-center py-8">
        No AI predictions available yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Zap size={18} className="text-primary-600" />
        <h3 className="font-semibold text-slate-800">AI Multi-Modal Analysis</h3>
      </div>
      {predictions.map((p) => (
        <PredictionCard key={p.id} prediction={p} />
      ))}
    </div>
  );
}
