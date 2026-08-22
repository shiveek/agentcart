import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { merchantService } from "../../services/merchantService";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { EmptyState } from "../../components/common/EmptyState";
import { Sparkles, ArrowRight, TrendingUp, CheckCircle, Eye } from "lucide-react";

export const Opportunities = () => {
  const { merchantId } = useAuth();
  const [relationships, setRelationships] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadOpportunities = async () => {
      if (!merchantId) return;
      setLoading(true);
      try {
        const data = await merchantService.getRelationships(merchantId);
        setRelationships(data);
      } catch (err) {
        console.error("Failed to load revenue opportunities:", err);
      } finally {
        setLoading(false);
      }
    };
    loadOpportunities();
  }, [merchantId]);

  if (loading) {
    return <LoadingSpinner text="Analyzing AI cross-sell opportunities..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <h1 className="text-2xl font-bold text-slate-100 flex items-center space-x-2">
          <Sparkles className="w-6 h-6 text-brand-400" />
          <span>Opportunity Center</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          AI-generated cross-sell, upsell, and frequently-bought-together recommendation rules
        </p>
      </div>

      {/* Info Alert */}
      <div className="p-4 bg-brand-500/10 border border-brand-500/20 rounded-xl text-xs text-brand-300 flex items-start space-x-3">
        <Sparkles className="w-5 h-5 text-brand-400 shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-slate-100">AI Growth Engine Governance</p>
          <p className="text-slate-400 mt-0.5">
            Recommendation scores (e.g. 0.87) represent relationship confidence derived from catalog graph rules. Realized revenue is strictly computed from confirmed server transactions.
          </p>
        </div>
      </div>

      {/* Opportunity Cards List */}
      {relationships.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No product relationship rules configured"
          description="Add product relationships to trigger automated AI agent cross-sells."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {relationships.map((rel) => {
            const source = rel.source_product;
            const target = rel.target_product;
            const expectedVal = target ? parseFloat(target.price).toFixed(2) : "0.00";

            return (
              <Card key={rel.id} className="relative group hover:border-brand-500/40 transition">
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-1 bg-brand-500/10 text-brand-400 border border-brand-500/20 text-[11px] font-semibold rounded-lg uppercase tracking-wider">
                    {rel.relationship_type.replace("_", " ")}
                  </span>
                  <Badge status={rel.is_active ? "ACTIVE" : "FAILED"}>
                    {rel.is_active ? "ENABLED" : "DISABLED"}
                  </Badge>
                </div>

                <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 mb-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-400">Trigger Product</p>
                      <p className="font-bold text-slate-100 text-sm mt-0.5">{source?.name || "Source Item"}</p>
                      <p className="text-[10px] font-mono text-slate-500">₹{parseFloat(source?.price || 0).toFixed(2)}</p>
                    </div>

                    <div className="px-2 text-slate-500">
                      <ArrowRight className="w-5 h-5" />
                    </div>

                    <div className="text-right">
                      <p className="text-xs text-slate-400">Recommended Add-on</p>
                      <p className="font-bold text-brand-400 text-sm mt-0.5">{target?.name || "Target Item"}</p>
                      <p className="text-[10px] font-mono text-slate-500">₹{expectedVal}</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Recommendation Score:</span>
                    <span className="font-bold text-emerald-400">{rel.score}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">AI Recommendation Reason:</span>
                    <span className="text-slate-200 font-medium">{rel.reason || "Frequently bought together"}</span>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                    <span className="text-slate-400">Expected Additional Order Value:</span>
                    <span className="font-bold text-slate-100 flex items-center text-sm">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400 mr-1" /> +₹{expectedVal}
                    </span>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center justify-end space-x-2">
                  <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition flex items-center space-x-1">
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Graph</span>
                  </button>
                  <button className="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white text-xs font-medium rounded-lg transition flex items-center space-x-1">
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Active in AI Agent</span>
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
