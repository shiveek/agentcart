import React from "react";

export const Card = ({ children, className = "", title, subtitle, action }) => {
  return (
    <div className={`bg-slate-900/80 border border-slate-800/80 rounded-xl p-5 shadow-xl backdrop-blur-sm ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800/60">
          <div>
            {title && <h3 className="text-base font-semibold text-slate-100">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
