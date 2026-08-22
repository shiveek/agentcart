import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Bot, LogOut, ShieldCheck, User as UserIcon } from "lucide-react";

export const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <Link to="/" className="flex items-center space-x-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-lg text-white tracking-tight">AgentCart</span>
            <span className="ml-2 px-1.5 py-0.5 text-[10px] font-semibold bg-brand-500/10 text-brand-400 border border-brand-500/20 rounded">
              AI-Native Commerce
            </span>
          </div>
        </Link>
      </div>

      <div className="flex items-center space-x-4">
        <Link
          to="/buyer"
          className="flex items-center space-x-2 text-xs font-semibold px-3 py-2 rounded-lg bg-brand-500/10 text-brand-400 border border-brand-500/30 hover:bg-brand-500/20 transition"
        >
          <Bot className="w-4 h-4" />
          <span>Launch AI Buyer Demo</span>
        </Link>

        {isAuthenticated ? (
          <div className="flex items-center space-x-3 pl-3 border-l border-slate-800">
            <div className="flex items-center space-x-2 text-xs">
              <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-slate-300">
                <UserIcon className="w-4 h-4" />
              </div>
              <div className="hidden sm:block text-left">
                <p className="font-medium text-slate-200">{user?.email}</p>
                <p className="text-[10px] text-slate-400 capitalize">{user?.role?.replace("_", " ")}</p>
              </div>
            </div>
            <button
              onClick={logout}
              title="Logout"
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center space-x-2 text-xs">
            <Link
              to="/login"
              className="px-3 py-1.5 text-slate-300 hover:text-white transition"
            >
              Log In
            </Link>
            <Link
              to="/register"
              className="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white font-medium rounded-lg transition"
            >
              Register Merchant
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};
