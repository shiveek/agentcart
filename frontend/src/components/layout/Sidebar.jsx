import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  Sparkles,
  ShieldAlert,
  Receipt,
  History,
  Bot,
} from "lucide-react";

export const Sidebar = () => {
  const merchantNavItems = [
    { label: "Dashboard", path: "/merchant/dashboard", icon: LayoutDashboard },
    { label: "Products", path: "/merchant/products", icon: Package },
    { label: "Opportunities", path: "/merchant/opportunities", icon: Sparkles },
    { label: "Policies", path: "/merchant/policies", icon: ShieldAlert },
    { label: "Transactions", path: "/merchant/transactions", icon: Receipt },
    { label: "Audit Trail", path: "/merchant/audit", icon: History },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/60 flex flex-col justify-between hidden md:flex min-h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-6">
        <div>
          <p className="px-3 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Merchant Governance
          </p>
          <nav className="space-y-1">
            {merchantNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition ${
                      isActive
                        ? "bg-brand-600/15 text-brand-400 border border-brand-500/20 shadow-sm"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        <div>
          <p className="px-3 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
            AI Buyer Experience
          </p>
          <NavLink
            to="/buyer"
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition ${
                isActive
                  ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20 shadow-sm"
                  : "text-emerald-400/80 hover:text-emerald-300 hover:bg-emerald-500/10"
              }`
            }
          >
            <Bot className="w-4 h-4" />
            <span>AI Shopping Agent</span>
          </NavLink>
        </div>
      </div>

      <div className="p-4 border-t border-slate-800/80">
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/60 text-xs">
          <p className="font-semibold text-slate-300">AgentCart Engine</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Policy & Razorpay Governed</p>
        </div>
      </div>
    </aside>
  );
};
