import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { merchantService } from "../../services/merchantService";
import { Card } from "../../components/common/Card";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { ShieldCheck, ShieldAlert, Zap, CheckCircle2, Lock, AlertTriangle } from "lucide-react";

export const Policies = () => {
  const { merchantId } = useAuth();
  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  const [formData, setFormData] = useState({
    max_transaction_amount: "5000.00",
    max_discount_percent: "10.00",
    approval_threshold: "3000.00",
    require_buyer_confirmation: true,
    enable_cross_sell: true,
    enable_upsell: true,
    max_payment_retries: 2,
  });

  useEffect(() => {
    const loadPolicy = async () => {
      if (!merchantId) return;
      setLoading(true);
      try {
        const data = await merchantService.getPolicy(merchantId);
        setPolicy(data);
        setFormData({
          max_transaction_amount: data.max_transaction_amount,
          max_discount_percent: data.max_discount_percent,
          approval_threshold: data.approval_threshold,
          require_buyer_confirmation: data.require_buyer_confirmation,
          enable_cross_sell: data.enable_cross_sell,
          enable_upsell: data.enable_upsell,
          max_payment_retries: data.max_payment_retries,
        });
      } catch (err) {
        console.error("Failed to load merchant policy:", err);
      } finally {
        setLoading(false);
      }
    };
    loadPolicy();
  }, [merchantId]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage({ type: "", text: "" });
    try {
      const updated = await merchantService.updatePolicy(merchantId, formData);
      setPolicy(updated);
      setMessage({ type: "success", text: "Merchant policy governance rules updated successfully." });
    } catch (err) {
      console.error("Failed to update policy:", err);
      setMessage({ type: "error", text: err.response?.data?.detail || "Failed to update merchant policy." });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading Policy Engine governance rules..." />;
  }

  const maxTx = parseFloat(formData.max_transaction_amount || 5000);
  const appThresh = parseFloat(formData.approval_threshold || 3000);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <h1 className="text-2xl font-bold text-slate-100 flex items-center space-x-2">
          <ShieldCheck className="w-6 h-6 text-brand-400" />
          <span>Policy Engine & Governance</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure deterministic server-side safety bounds for AI Agent transactions
        </p>
      </div>

      {message.text && (
        <div
          className={`p-4 rounded-xl text-xs font-medium border flex items-center space-x-2 ${
            message.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              : "bg-rose-500/10 border-rose-500/20 text-rose-400"
          }`}
        >
          {message.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Visual Safety Bounds Diagram for Judges */}
      <Card title="Visual Policy Safety Boundaries" subtitle="How Policy Engine evaluates incoming AI buyer transactions">
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
              <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm mb-1">
                <CheckCircle2 className="w-4 h-4" />
                <span>ALLOW</span>
              </div>
              <p className="font-semibold text-slate-200">Below ₹{appThresh.toFixed(0)}</p>
              <p className="text-[11px] text-slate-400 mt-1">
                Processed instantly without human review. Policy Engine returns <code>READY_FOR_PAYMENT</code>.
              </p>
            </div>

            <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
              <div className="flex items-center space-x-2 text-amber-400 font-bold text-sm mb-1">
                <AlertTriangle className="w-4 h-4" />
                <span>ALLOW WITH APPROVAL</span>
              </div>
              <p className="font-semibold text-slate-200">₹{appThresh.toFixed(0)} – ₹{maxTx.toFixed(0)}</p>
              <p className="text-[11px] text-slate-400 mt-1">
                Held in <code>AWAITING_APPROVAL</code>. Requires merchant admin approval before payment order creation.
              </p>
            </div>

            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl">
              <div className="flex items-center space-x-2 text-rose-400 font-bold text-sm mb-1">
                <Lock className="w-4 h-4" />
                <span>BLOCK</span>
              </div>
              <p className="font-semibold text-slate-200">Above ₹{maxTx.toFixed(0)}</p>
              <p className="text-[11px] text-slate-400 mt-1">
                Hard safety block. Transaction is rejected automatically with clear policy reason.
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Policy Form */}
      <Card title="Merchant Policy Configuration Form">
        <form onSubmit={handleSubmit} className="space-y-6 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block font-medium text-slate-300 mb-1.5">
                Maximum AI Transaction Limit (₹)
              </label>
              <input
                type="number"
                step="100"
                name="max_transaction_amount"
                value={formData.max_transaction_amount}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-100 font-mono focus:outline-none focus:border-brand-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Transactions above this value are automatically BLOCKED by server.
              </p>
            </div>

            <div>
              <label className="block font-medium text-slate-300 mb-1.5">
                Approval Threshold (₹)
              </label>
              <input
                type="number"
                step="100"
                name="approval_threshold"
                value={formData.approval_threshold}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-100 font-mono focus:outline-none focus:border-brand-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Transactions above this value require explicit merchant review.
              </p>
            </div>

            <div>
              <label className="block font-medium text-slate-300 mb-1.5">
                Maximum AI Discount (%)
              </label>
              <input
                type="number"
                step="0.5"
                name="max_discount_percent"
                value={formData.max_discount_percent}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-100 font-mono focus:outline-none focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-300 mb-1.5">
                Max Payment Retries Allowed
              </label>
              <input
                type="number"
                name="max_payment_retries"
                value={formData.max_payment_retries}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-100 font-mono focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800/80 space-y-3">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                name="require_buyer_confirmation"
                checked={formData.require_buyer_confirmation}
                onChange={handleChange}
                className="rounded border-slate-800 bg-slate-950 text-brand-600 focus:ring-brand-500"
              />
              <div>
                <span className="font-semibold text-slate-200">Require Buyer Confirmation</span>
                <p className="text-[11px] text-slate-400">Enforce explicit checkout confirmation before initiating payment.</p>
              </div>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                name="enable_cross_sell"
                checked={formData.enable_cross_sell}
                onChange={handleChange}
                className="rounded border-slate-800 bg-slate-950 text-brand-600 focus:ring-brand-500"
              />
              <div>
                <span className="font-semibold text-slate-200">Enable Automated Cross-Sell Recommendations</span>
                <p className="text-[11px] text-slate-400">Allow AI Agent to suggest complementary products during conversation.</p>
              </div>
            </label>
          </div>

          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-medium text-xs rounded-xl shadow-lg shadow-brand-600/25 transition"
            >
              {saving ? "Saving Policy..." : "Save Governance Rules"}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
};
