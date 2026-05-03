type InfoBoxType = "info" | "warning" | "tip" | "success" | "error";

interface InfoBoxProps {
  type?: InfoBoxType;
  title?: string;
  children: React.ReactNode;
}

const CONFIG: Record<InfoBoxType, { icon: string; borderColor: string; bgColor: string; iconColor: string; titleColor: string }> = {
  info:    { icon: "ℹ️", borderColor: "border-sky-500/30",   bgColor: "bg-sky-500/5",   iconColor: "text-sky-400",   titleColor: "text-sky-300" },
  warning: { icon: "⚠️", borderColor: "border-yellow-500/30", bgColor: "bg-yellow-500/5", iconColor: "text-yellow-400", titleColor: "text-yellow-300" },
  tip:     { icon: "💡", borderColor: "border-teal-500/30",  bgColor: "bg-teal-500/5",  iconColor: "text-teal-400",  titleColor: "text-teal-300" },
  success: { icon: "✅", borderColor: "border-green-500/30", bgColor: "bg-green-500/5", iconColor: "text-green-400", titleColor: "text-green-300" },
  error:   { icon: "❌", borderColor: "border-red-500/30",   bgColor: "bg-red-500/5",   iconColor: "text-red-400",   titleColor: "text-red-300" },
};

export default function InfoBox({ type = "info", title, children }: InfoBoxProps) {
  const { icon, borderColor, bgColor, iconColor, titleColor } = CONFIG[type];
  return (
    <div className={`flex gap-3 p-4 rounded-lg border ${borderColor} ${bgColor} my-4`}>
      <span className={`flex-shrink-0 text-lg ${iconColor}`}>{icon}</span>
      <div>
        {title && <p className={`font-semibold text-sm mb-1 ${titleColor}`}>{title}</p>}
        <div className="text-sm text-slate-300 leading-relaxed">{children}</div>
      </div>
    </div>
  );
}
