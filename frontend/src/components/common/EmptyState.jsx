import React from "react";
import { PackageOpen } from "lucide-react";

export const EmptyState = ({
  icon: Icon = PackageOpen,
  title = "No data available",
  description = "Not enough transaction or record data yet.",
  action,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-slate-900/40 border border-dashed border-slate-800 rounded-xl my-4">
      <div className="p-3 bg-slate-800/60 rounded-full text-slate-400 mb-3">
        <Icon className="w-6 h-6" />
      </div>
      <h4 className="text-sm font-semibold text-slate-200 mb-1">{title}</h4>
      <p className="text-xs text-slate-400 max-w-sm mb-4">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};
