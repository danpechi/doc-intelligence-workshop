"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

interface NavItem {
  href: string;
  label: string;
  description: string;
  icon: string;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    href: "/",
    label: "Setup",
    description: "Select industry & initialize dataset",
    icon: "🏠",
  },
  {
    href: "/structured-extraction",
    label: "Structured Extraction",
    description: "ai_query with responseFormat",
    icon: "🔍",
    badge: "ai_query",
  },
  {
    href: "/classification",
    label: "Classification",
    description: "ai_classify & ai_extract",
    icon: "🏷️",
    badge: "ai_classify",
  },
  {
    href: "/parse-document",
    label: "Document Parsing",
    description: "ai_parse_document from volumes",
    icon: "📄",
    badge: "NEW",
  },
  {
    href: "/fuzzy-matching",
    label: "Semantic Matching",
    description: "ai_similarity & Vector Search",
    icon: "🔗",
    badge: "ai_similarity",
  },
  {
    href: "/lakeflow",
    label: "Production Pipeline",
    description: "Lakeflow Declarative Pipelines",
    icon: "⚙️",
    badge: "DLT",
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className="hidden lg:flex flex-col sticky top-0 h-screen transition-all duration-300 border-r border-slate-700/50"
      style={{
        width: collapsed ? "64px" : "280px",
        backgroundColor: "var(--color-navy)",
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-slate-700/50 min-h-[64px]">
        <div
          className="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center font-bold text-sm text-white"
          style={{ background: "linear-gradient(135deg, #FF6B35, #FF8C5A)" }}
        >
          DB
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <p className="text-white font-semibold text-sm leading-tight">AI Functions</p>
            <p className="text-slate-400 text-xs">Workshop</p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto flex-shrink-0 text-slate-400 hover:text-white transition-colors p-1 rounded"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? "→" : "←"}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={`
                flex items-start gap-3 px-3 py-3 rounded-lg mb-1 transition-all duration-150
                ${isActive
                  ? "bg-orange-500/10 border border-orange-500/30 text-orange-400"
                  : "text-slate-300 hover:bg-slate-700/50 hover:text-white border border-transparent"
                }
              `}
            >
              <span className="text-xl flex-shrink-0 mt-0.5">{item.icon}</span>
              {!collapsed && (
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm truncate">{item.label}</span>
                    {item.badge && (
                      <span
                        className={`
                          flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold
                          ${item.badge === "NEW"
                            ? "bg-green-500/20 text-green-400 border border-green-500/30"
                            : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                          }
                        `}
                      >
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 truncate mt-0.5">{item.description}</p>
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-slate-700/50">
          <p className="text-xs text-slate-500">
            Databricks AI Functions Workshop
          </p>
          <p className="text-xs text-slate-600 mt-0.5">
            Built with Databricks Apps + DAB
          </p>
        </div>
      )}
    </aside>
  );
}
