import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Databricks AI Functions Workshop",
  description:
    "Interactive workshop: ai_query, ai_classify, ai_extract, ai_parse_document, and semantic matching at scale on Databricks",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 flex flex-col min-h-screen">
            {/* Mobile header */}
            <header
              className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-slate-700/50"
              style={{ backgroundColor: "var(--color-navy)" }}
            >
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs text-white"
                style={{ background: "linear-gradient(135deg, #FF6B35, #FF8C5A)" }}
              >
                DB
              </div>
              <span className="text-white font-semibold text-sm">AI Functions Workshop</span>
            </header>

            {/* Page content */}
            <div className="flex-1 overflow-y-auto">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
