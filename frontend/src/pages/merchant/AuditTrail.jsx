import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { auditService } from "../../services/auditService";
import { Card } from "../../components/common/Card";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { EmptyState } from "../../components/common/EmptyState";
import { History, Shield, Bot, User, Server, ChevronDown, ChevronRight } from "lucide-react";

export const AuditTrail = () => {
  const { merchantId } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedLogId, setExpandedLogId] = useState(null);

  useEffect(() => {
    const loadAuditLogs = async () => {
      if (!merchantId) return;
      setLoading(true);
      try {
        const data = await auditService.getAuditLogs(merchantId, 100);
        setLogs(data);
      } catch (err) {
        console.error("Failed to load audit logs:", err);
      } finally {
        setLoading(false);
      }
    };
    loadAuditLogs();
  }, [merchantId]);

  if (loading) {
    return <LoadingSpinner text="Loading system audit log timeline..." />;
  }

  const getActorIcon = (actorType) => {
    switch (actorType) {
      case "AI_AGENT":
        return <Bot className="w-4 h-4 text-emerald-400" />;
      case "USER":
        return <User className="w-4 h-4 text-brand-400" />;
      case "WEBHOOK":
        return <Server className="w-4 h-4 text-amber-400" />;
      default:
        return <Shield className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <h1 className="text-2xl font-bold text-slate-100 flex items-center space-x-2">
          <History className="w-6 h-6 text-brand-400" />
          <span>Audit Trail & Security Timeline</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Complete immutable record of all AI agent, user, policy, and Razorpay webhook events
        </p>
      </div>

      {/* Audit Log Timeline */}
      <Card title="System Event Stream" subtitle="Sanitized audit logs with secret redaction">
        {logs.length === 0 ? (
          <EmptyState
            icon={History}
            title="No audit events recorded yet"
            description="All platform interactions will be recorded in this timeline."
          />
        ) : (
          <div className="space-y-3">
            {logs.map((log) => {
              const isExpanded = expandedLogId === log.id;
              return (
                <div
                  key={log.id}
                  className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 transition hover:border-slate-700"
                >
                  <div
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                        {getActorIcon(log.actor_type)}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs font-bold text-brand-400">
                            {log.action}
                          </span>
                          <span className="px-2 py-0.5 bg-slate-800 text-[10px] text-slate-400 font-semibold rounded">
                            {log.actor_type}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Actor ID: <span className="font-mono text-slate-300">{log.actor_id}</span>
                          {log.resource_type && (
                            <span className="ml-2">• Resource: {log.resource_type} ({log.resource_id?.slice(0, 8)})</span>
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <span className="text-xs text-slate-500 font-mono">
                        {new Date(log.created_at).toLocaleString([], {
                          dateStyle: "short",
                          timeStyle: "medium",
                        })}
                      </span>
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Metadata JSON Viewer */}
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-slate-800/60">
                      <p className="text-[11px] font-semibold text-slate-400 mb-1.5">
                        Sanitized Event Metadata:
                      </p>
                      <pre className="bg-slate-900 p-3 rounded-lg text-[11px] font-mono text-emerald-400 overflow-x-auto border border-slate-800">
                        {JSON.stringify(log.metadata || {}, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
};
