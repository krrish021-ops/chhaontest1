"use client";

import React, { useState } from "react";
import { FileText, Download, Loader2, CheckCircle2, X, AlertCircle } from "lucide-react";

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  cityId: string;
}

export const ReportModal: React.FC<ReportModalProps> = ({ isOpen, onClose, cityId }) => {
  const [loading, setLoading] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setPdfUrl(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/report/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          city_id: cityId,
          include_scenarios: true,
          department: "Municipal Town Planning & Climate Resilience Cell",
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to compile PDF report from backend.");
      }

      const data = await res.json();
      setPdfUrl(`http://localhost:8000${data.report_url}`);
      setFileSize(data.file_size_kb);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-lg rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl text-slate-100">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center space-x-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-600/20 text-orange-500 border border-orange-500/30">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold">Generate Thermal Audit PDF</h2>
            <p className="text-xs text-slate-400">
              Statutory Planning & Heat Action Plan Report for {cityId.toUpperCase()}
            </p>
          </div>
        </div>

        {/* Contents Description */}
        <div className="space-y-3 text-xs text-slate-300 bg-slate-800/60 p-3.5 rounded-lg border border-slate-700/50 mb-5">
          <div className="font-semibold text-orange-400">Included Sections:</div>
          <ul className="list-disc list-inside space-y-1 text-slate-300">
            <li>Executive Summary & citywide nocturnal SUHII metrics</li>
            <li>Top-decile critical hotspot ranking table</li>
            <li>SHAP feature attribution & driver explainability</li>
            <li>Simulated counterfactual mitigation scenarios & costs</li>
            <li>Statutory signature blocks for standing committees</li>
          </ul>
        </div>

        {/* Error State */}
        {error && (
          <div className="flex items-center space-x-2 text-xs text-red-400 bg-red-950/40 p-3 rounded-lg border border-red-800/40 mb-4">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Action / Success State */}
        {pdfUrl ? (
          <div className="space-y-4">
            <div className="flex items-center space-x-2 text-xs text-green-400 bg-green-950/40 p-3 rounded-lg border border-green-800/40">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>Thermal Audit Report compiled successfully ({fileSize} KB).</span>
            </div>
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex w-full items-center justify-center space-x-2 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-green-500 transition"
            >
              <Download className="w-4 h-4" />
              <span>Download PDF Audit</span>
            </a>
          </div>
        ) : (
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="flex w-full items-center justify-center space-x-2 rounded-lg bg-orange-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-orange-500 disabled:opacity-50 transition"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Compiling Charts & Report...</span>
              </>
            ) : (
              <>
                <FileText className="w-4 h-4" />
                <span>Compile Official PDF</span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};
