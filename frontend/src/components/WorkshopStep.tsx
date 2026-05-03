interface WorkshopStepProps {
  number: number;
  title: string;
  children: React.ReactNode;
  isCompleted?: boolean;
}

export default function WorkshopStep({ number, title, children, isCompleted }: WorkshopStepProps) {
  return (
    <div className="relative mb-10">
      <div className="flex items-start gap-5">
        {/* Badge */}
        <div
          className={`
            flex-shrink-0 w-11 h-11 rounded-full flex items-center justify-center
            font-bold text-white shadow-lg text-sm
            ${isCompleted
              ? "bg-green-500"
              : "bg-gradient-to-br from-orange-500 to-orange-600"
            }
          `}
        >
          {isCompleted ? "✓" : number}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h2 className="text-xl font-semibold text-white mb-4 leading-tight">{title}</h2>
          <div
            className="rounded-xl p-6 border border-slate-700/60"
            style={{ backgroundColor: "var(--color-navy-light)" }}
          >
            {children}
          </div>
        </div>
      </div>

      {/* Connector line */}
      <div
        className="absolute left-5 top-11 w-0.5 bg-slate-700/50"
        style={{ height: "calc(100% - 2.75rem)" }}
      />
    </div>
  );
}
