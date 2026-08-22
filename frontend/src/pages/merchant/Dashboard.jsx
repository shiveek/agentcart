import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { orderService } from "../../services/orderService";
import { merchantService } from "../../services/merchantService";
import { auditService } from "../../services/auditService";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import { EmptyState } from "../../components/common/EmptyState";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import {
  TrendingUp,
  ShoppingBag,
  DollarSign,
  Bot,
  ShieldCheck,
  Zap,
  ArrowUpRight,
  ArrowRight,
} from "lucide-react";
import { Link } from "react-router-dom";

export const Dashboard = () => {
  const { merchantId } = useAuth();
  const [orders, setOrders] = useState([]);
  const [policy, setPolicy] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      if (!merchantId) return;
      setLoading(true);
      try {
        const [ordersData, policyData, auditData] = await Promise.all([
          orderService.getOrders(merchantId).catch(() => []),
          merchantService.getPolicy(merchantId).catch(() => null),
          auditService.getAuditLogs(merchantId, 10).catch(() => []),
        ]);
        setOrders(ordersData);
        setPolicy(policyData);
        setAuditLogs(auditData);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    loadDashboardData();
  }, [merchantId]);

  if (loading) {
    return <LoadingSpinner text="Loading merchant dashboard data..." />;
  }

  // Calculate real metrics
  const paidOrders = orders.filter((o) => o.status === "PAID");
  const totalRevenue = paidOrders.reduce((sum, o) => sum + parseFloat(o.total || 0), 0);
  const totalOrdersCount = orders.length;
  const avgOrderValue = paidOrders.length > 0 ? totalRevenue / paidOrders.length : 0;

  const aiOrders = paidOrders.filter((o) => o.policy_status !== "NONE" || o.customer_identifier?.includes("buyer"));
  const aiRevenue = aiOrders.reduce((sum, o) => sum + parseFloat(o.total || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Merchant Governance Overview</h1>
          <p className="text-xs text-slate-400 mt-1">Real-time revenue, AI transaction analytics, and Policy Engine governance</p>
        </div>
        <Link
          to="/buyer"
          className="inline-flex items-center space-x-2 text-xs font-semibold px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 text-white shadow-lg shadow-brand-600/20 hover:from-brand-500 hover:to-brand-400 transition self-start sm:self-auto"
        >
          <Bot className="w-4 h-4" />
          <span>Launch AI Buyer Simulator</span>
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Total Revenue</p>
              <p className="text-2xl font-bold text-slate-100 mt-1">
                ₹{totalRevenue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="p-3 bg-brand-500/10 text-brand-400 rounded-xl">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-[11px] text-slate-400">
            <span className="text-emerald-400 font-semibold flex items-center mr-1">
              <TrendingUp className="w-3 h-3 mr-0.5" /> +12.4%
            </span>
            <span>vs previous period</span>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Total Orders</p>
              <p className="text-2xl font-bold text-slate-100 mt-1">{totalOrdersCount}</p>
            </div>
            <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl">
              <ShoppingBag className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-[11px] text-slate-400">
            <span className="text-slate-300 font-semibold">{paidOrders.length} Paid</span>
            <span className="mx-1.5">•</span>
            <span>{orders.filter((o) => o.status === "AWAITING_APPROVAL").length} Pending Approval</span>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Average Order Value (AOV)</p>
              <p className="text-2xl font-bold text-slate-100 mt-1">
                ₹{avgOrderValue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="p-3 bg-amber-500/10 text-amber-400 rounded-xl">
              <Zap className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 text-[11px] text-slate-400">
            Based on completed database transactions
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">AI-Assisted Revenue</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">
                ₹{aiRevenue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl">
              <Bot className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center text-[11px] text-slate-400">
            <span className="text-emerald-400 font-semibold mr-1">
              {totalRevenue > 0 ? Math.round((aiRevenue / totalRevenue) * 100) : 0}%
            </span>
            <span>of total store revenue</span>
          </div>
        </Card>
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Transactions & Opportunities */}
        <div className="lg:col-span-2 space-y-6">
          <Card
            title="Recent Merchant Transactions"
            subtitle="Live status of internal orders governed by Policy Engine"
            action={
              <Link to="/merchant/transactions" className="text-xs text-brand-400 hover:underline flex items-center font-medium">
                View All <ArrowUpRight className="w-3.5 h-3.5 ml-0.5" />
              </Link>
            }
          >
            {orders.length === 0 ? (
              <EmptyState
                title="Not enough transaction data yet"
                description="Use the AI Buyer Demo to generate simulated shopping transactions."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-medium pb-2">
                      <th className="pb-3 font-medium">Order ID</th>
                      <th className="pb-3 font-medium">Customer</th>
                      <th className="pb-3 font-medium">Amount</th>
                      <th className="pb-3 font-medium">Policy Status</th>
                      <th className="pb-3 font-medium">Order Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {orders.slice(0, 5).map((order) => (
                      <tr key={order.id} className="hover:bg-slate-800/30 transition">
                        <td className="py-3 font-mono text-slate-300">
                          #{order.id.slice(0, 8)}
                        </td>
                        <td className="py-3 text-slate-300">
                          {order.customer_identifier || "Anonymous"}
                        </td>
                        <td className="py-3 font-semibold text-slate-100">
                          ₹{parseFloat(order.total).toFixed(2)}
                        </td>
                        <td className="py-3">
                          <Badge status={order.policy_status} />
                        </td>
                        <td className="py-3">
                          <Badge status={order.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* AI Opportunity Card */}
          <Card
            title="Active AI Revenue Opportunities"
            subtitle="Automated cross-sell & recommendation rules in effect"
            action={
              <Link to="/merchant/opportunities" className="text-xs text-brand-400 hover:underline flex items-center font-medium">
                Opportunity Center <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
              </Link>
            }
          >
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl flex items-start justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-slate-200 text-sm">Mechanical Keyboard</span>
                  <span className="text-slate-500">+</span>
                  <span className="font-semibold text-brand-400 text-sm">Wireless Mouse</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Cross-sell recommendation score: <strong className="text-slate-200">0.87</strong> (Frequently bought together)
                </p>
                <p className="text-xs text-emerald-400 mt-2 font-medium">
                  Expected Additional Order Value: +₹699.00
                </p>
              </div>
              <Badge status="ACTIVE">Enabled</Badge>
            </div>
          </Card>
        </div>

        {/* Right 1 Col: Security Policy Summary & Agent Activity */}
        <div className="space-y-6">
          <Card title="Security & Policy Bounds" subtitle="Server-enforced AI transaction parameters">
            {policy ? (
              <div className="space-y-4 text-xs">
                <div className="flex items-center justify-between p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80">
                  <span className="text-slate-400">Max Transaction Limit:</span>
                  <span className="font-bold text-slate-100">₹{parseFloat(policy.max_transaction_amount).toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80">
                  <span className="text-slate-400">Approval Threshold:</span>
                  <span className="font-bold text-amber-400">₹{parseFloat(policy.approval_threshold).toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80">
                  <span className="text-slate-400">Max Payment Retries:</span>
                  <span className="font-bold text-slate-100">{policy.max_payment_retries} attempts</span>
                </div>
                <div className="flex items-center justify-between p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80">
                  <span className="text-slate-400">Buyer Confirmation:</span>
                  <span className="font-bold text-emerald-400">{policy.require_buyer_confirmation ? "Required" : "Optional"}</span>
                </div>

                <div className="p-3 bg-brand-500/10 border border-brand-500/20 rounded-xl text-[11px] text-brand-300">
                  <ShieldCheck className="w-4 h-4 text-brand-400 mb-1" />
                  Transactions above ₹{parseFloat(policy.approval_threshold).toFixed(0)} require merchant approval. Transactions above ₹{parseFloat(policy.max_transaction_amount).toFixed(0)} are blocked.
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400">Loading policy bounds...</p>
            )}
          </Card>

          {/* Real Audit Stream */}
          <Card title="Live Agent & System Audit Stream" subtitle="Recent governance event log">
            {auditLogs.length === 0 ? (
              <EmptyState title="No audit logs recorded yet" description="System actions will stream here." />
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
                {auditLogs.slice(0, 6).map((log) => (
                  <div key={log.id} className="p-2.5 bg-slate-950/40 border border-slate-800/60 rounded-lg text-xs flex items-start justify-between">
                    <div>
                      <span className="font-mono text-[10px] text-brand-400 font-semibold">{log.action}</span>
                      <p className="text-[11px] text-slate-400 mt-0.5">{log.actor_type}: {log.actor_id}</p>
                    </div>
                    <span className="text-[10px] text-slate-500">
                      {new Date(log.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
