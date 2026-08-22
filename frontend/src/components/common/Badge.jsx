import React from "react";

const statusVariants = {
  APPROVED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  PAID: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  CAPTURED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  SUCCESS: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  ALLOW: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",

  AWAITING_APPROVAL: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  ALLOW_WITH_APPROVAL: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  PAYMENT_PENDING: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  CREATED: "bg-brand-500/10 text-brand-400 border-brand-500/20",
  ACTIVE: "bg-brand-500/10 text-brand-400 border-brand-500/20",

  BLOCKED: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  PAYMENT_FAILED: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  FAILED: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  CANCELLED: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  REJECTED: "bg-rose-500/10 text-rose-400 border-rose-500/20",

  DEFAULT: "bg-slate-800 text-slate-300 border-slate-700",
};

export const Badge = ({ children, status, className = "" }) => {
  const normalizedStatus = (status || children || "").toString().toUpperCase();
  const variant = statusVariants[normalizedStatus] || statusVariants.DEFAULT;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variant} ${className}`}
    >
      {children || status}
    </span>
  );
};
