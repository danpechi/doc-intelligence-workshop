"use client";

import { useState } from "react";

interface CodeBlockProps {
  code: string;
  language?: string;
  title?: string;
  filename?: string;
}

export default function CodeBlock({ code, language = "sql", title, filename }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      console.error("Copy failed");
    }
  }

  return (
    <div className="rounded-lg overflow-hidden border border-slate-700/60 my-4" style={{ backgroundColor: "#0d1117" }}>
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-700/60" style={{ backgroundColor: "#161b22" }}>
        <span className="w-3 h-3 rounded-full bg-red-500/70" />
        <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
        <span className="w-3 h-3 rounded-full bg-green-500/70" />
        <span className="flex-1 text-slate-400 text-sm ml-2 font-mono">
          {filename || title || language}
        </span>
        <span className="text-xs font-mono uppercase tracking-wide text-slate-500 bg-slate-700/50 px-2 py-0.5 rounded">
          {language}
        </span>
        <button
          onClick={handleCopy}
          className={`text-xs px-2.5 py-1 rounded transition-colors font-mono ${
            copied
              ? "bg-green-500/20 text-green-400 border border-green-500/30"
              : "bg-slate-700/50 text-slate-300 hover:bg-slate-600/50 border border-slate-600/30"
          }`}
        >
          {copied ? "✓ Copied!" : "Copy"}
        </button>
      </div>

      {/* Code */}
      <pre className="overflow-x-auto p-4 text-sm leading-relaxed">
        <code className="text-slate-200 font-mono">{code}</code>
      </pre>
    </div>
  );
}
