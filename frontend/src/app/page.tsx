"use client";

import { useState, useEffect } from "react";
import { useIndustry } from "@/lib/useIndustry";
import { INDUSTRY_KEYS, INDUSTRIES, type IndustryKey } from "@/lib/industryConfig";
import InfoBox from "@/components/InfoBox";

type SetupStatus = "idle" | "running" | "success" | "error";

export default function SetupPage() {
  const { industry, config, setIndustry, loaded } = useIndustry();
  const [status, setStatus] = useState<SetupStatus>("idle");
  const [runId, setRunId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState("");
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

  // Clean up polling on unmount
  useEffect(() => () => { if (pollInterval) clearInterval(pollInterval); }, [pollInterval]);

  async function handleSetup() {
    setStatus("running");
    setStatusMessage("Triggering setup job...");

    try {
      const res = await fetch("/api/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ industry }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Setup failed");
      }

      const data = await res.json();
      setRunId(data.run_id);
      setStatusMessage(`Job run started (run_id: ${data.run_id}). Setting up ${config.fullName} data...`);

      // Poll for status every 8 seconds
      const iv = setInterval(async () => {
        try {
          const statusRes = await fetch(`/api/setup/status/${data.run_id}`);
          const statusData = await statusRes.json();
          const lcState = statusData.life_cycle_state;
          const resultState = statusData.result_state;

          if (lcState === "TERMINATED") {
            clearInterval(iv);
            setPollInterval(null);
            if (resultState === "SUCCESS") {
              setStatus("success");
              setStatusMessage("Dataset initialized successfully! You can now proceed through the workshop tabs.");
            } else {
              setStatus("error");
              setStatusMessage(`Job failed: ${statusData.state_message || resultState}`);
            }
          } else {
            setStatusMessage(`Status: ${lcState} — ${statusData.state_message || "running..."}`);
          }
        } catch {
          // swallow polling errors
        }
      }, 8000);
      setPollInterval(iv);

    } catch (err: unknown) {
      setStatus("error");
      setStatusMessage(err instanceof Error ? err.message : "Unknown error");
    }
  }

  if (!loaded) return null;

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Hero */}
      <div className="mb-10">
        <div
          className="inline-flex items-center justify-center w-14 h-14 rounded-2xl text-3xl mb-5 shadow-lg"
          style={{ background: "linear-gradient(135deg, #FF6B35, #FF8C5A)" }}
        >
          🧠
        </div>
        <h1 className="text-4xl font-bold text-white mb-3">
          Databricks AI Functions Workshop
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl">
          Learn to apply AI at scale directly in SQL — no Python, no MLflow, no cluster setup.
          Pick your industry, initialize the dataset, then work through each lab.
        </p>
      </div>

      {/* What you'll learn */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
        {[
          { icon: "🔍", fn: "ai_query", desc: "Extract typed structs from any unstructured text using LLMs with responseFormat" },
          { icon: "🏷️", fn: "ai_classify / ai_extract", desc: "Zero-shot classification and named entity extraction without prompt engineering" },
          { icon: "📄", fn: "ai_parse_document", desc: "Parse PDFs, images, and Office files from UC Volumes directly in SQL" },
          { icon: "🔗", fn: "ai_similarity", desc: "Score pairwise semantic similarity for fuzzy matching and deduplication" },
          { icon: "🗄️", fn: "vector_search()", desc: "Find top-K semantically similar records from large Delta tables at millisecond latency" },
          { icon: "⚙️", fn: "Lakeflow Pipelines", desc: "Productionize all of the above with Auto Loader, quality gates, and incremental processing" },
        ].map((item) => (
          <div
            key={item.fn}
            className="p-4 rounded-xl border border-slate-700/50 hover:border-orange-500/30 transition-colors"
            style={{ backgroundColor: "var(--color-navy-light)" }}
          >
            <div className="text-2xl mb-2">{item.icon}</div>
            <p className="text-orange-400 font-mono text-sm font-semibold mb-1">{item.fn}</p>
            <p className="text-slate-400 text-xs leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>

      {/* Industry selector */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-white mb-2">
          Step 1 — Choose your industry vertical
        </h2>
        <p className="text-slate-400 text-sm mb-5">
          Each industry uses a different dataset and real-world use case. The same AI Functions apply across all of them.
          Your selection persists as you navigate through the workshop tabs.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {INDUSTRY_KEYS.map((key) => {
            const ind = INDUSTRIES[key];
            const isSelected = industry === key;
            return (
              <button
                key={key}
                onClick={() => setIndustry(key as IndustryKey)}
                className={`
                  text-left p-5 rounded-xl border-2 transition-all duration-150 hover:scale-[1.01]
                  ${isSelected
                    ? "border-orange-500 bg-orange-500/10 shadow-lg shadow-orange-500/10"
                    : "border-slate-700/50 hover:border-slate-500"
                  }
                `}
                style={{ backgroundColor: isSelected ? undefined : "var(--color-navy-light)" }}
              >
                <div className="text-3xl mb-3">{ind.icon}</div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-bold text-white">{ind.name}</span>
                  {isSelected && (
                    <span className="text-xs px-1.5 py-0.5 bg-orange-500 text-white rounded font-semibold">
                      Selected
                    </span>
                  )}
                </div>
                <p className="text-slate-400 text-xs leading-relaxed">{ind.tagline}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected industry detail */}
      <div
        className="rounded-xl border border-slate-700/50 p-6 mb-8"
        style={{ backgroundColor: "var(--color-navy-light)" }}
      >
        <h3 className="text-lg font-semibold text-white mb-3">
          {config.icon} {config.fullName}
        </h3>
        <p className="text-slate-300 text-sm leading-relaxed mb-4">{config.useCase}</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Tables", value: config.tables.join(", ") },
            { label: "Documents", value: config.documents },
            { label: "PDF Count", value: `${config.documentCount} files` },
            { label: "Primary AI Task", value: config.classifyLabels.slice(0, 3).join(", ") + "..." },
          ].map((item) => (
            <div key={item.label} className="bg-slate-800/50 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-1">{item.label}</p>
              <p className="text-slate-200 text-xs font-mono leading-relaxed">{item.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Setup button */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-white mb-2">
          Step 2 — Initialize the {config.name} dataset
        </h2>
        <p className="text-slate-400 text-sm mb-4">
          This will run a DAB job that creates the Unity Catalog schema, generates synthetic data,
          and uploads synthetic PDF documents to the volume for the{" "}
          <span className="text-white font-semibold">{config.fullName}</span> industry.
        </p>

        <InfoBox type="info" title="What gets created">
          <ul className="list-disc list-inside space-y-1 text-sm">
            <li>Schema: <code>main.ai_functions_workshop_{industry}</code></li>
            <li>Tables: {config.tables.map(t => <code key={t} className="mx-1">{t}</code>)}</li>
            <li>Volume: <code>/Volumes/main/ai_functions_workshop_{industry}/documents/</code></li>
            <li>{config.documentCount} synthetic PDFs for <code>ai_parse_document</code></li>
          </ul>
        </InfoBox>

        <div className="flex items-center gap-4 mt-4">
          <button
            onClick={handleSetup}
            disabled={status === "running"}
            className={`
              px-6 py-3 rounded-lg font-semibold text-white transition-all duration-150
              flex items-center gap-2
              ${status === "running"
                ? "opacity-60 cursor-not-allowed bg-slate-600"
                : "bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 shadow-lg hover:shadow-orange-500/20"
              }
            `}
          >
            {status === "running" && (
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            )}
            {status === "running"
              ? "Initializing..."
              : `Initialize ${config.name} Dataset`}
          </button>

          {status !== "idle" && (
            <div
              className={`
                flex-1 px-4 py-3 rounded-lg text-sm border
                ${status === "success" ? "border-green-500/30 bg-green-500/10 text-green-300" :
                  status === "error"   ? "border-red-500/30 bg-red-500/10 text-red-300" :
                  "border-blue-500/30 bg-blue-500/10 text-blue-300"}
              `}
            >
              {status === "running" && <span className="mr-2">⏳</span>}
              {status === "success" && <span className="mr-2">✅</span>}
              {status === "error"   && <span className="mr-2">❌</span>}
              {statusMessage}
              {runId && <span className="ml-2 text-xs opacity-70">[run_id: {runId}]</span>}
            </div>
          )}
        </div>

        {status === "success" && (
          <InfoBox type="success" title="Ready to start!">
            Your {config.fullName} dataset is initialized. Use the sidebar to navigate through the workshop labs.
            Start with <strong>Structured Extraction</strong> and work your way through.
          </InfoBox>
        )}
      </div>

      {/* DAB alternative */}
      <div
        className="rounded-xl border border-slate-700/50 p-6"
        style={{ backgroundColor: "var(--color-navy-light)" }}
      >
        <h3 className="text-slate-300 font-semibold mb-2">Or run via the CLI</h3>
        <p className="text-slate-400 text-xs mb-3">You can also trigger setup directly from the Databricks CLI:</p>
        <pre className="bg-slate-900 rounded-lg p-4 text-sm font-mono text-slate-200 overflow-x-auto">
{`# Deploy the bundle first (one-time)
databricks bundle deploy -e dev

# Initialize your chosen industry dataset
databricks bundle run setup_job --var industry=${industry} -e dev`}
        </pre>
      </div>
    </div>
  );
}
