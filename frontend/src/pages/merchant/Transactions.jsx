import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { orderService } from "../../services/orderService";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { EmptyState } from "../../components/common/EmptyState";
import { Receipt, Search, Filter, X, CheckCircle, XCircle, FileText, CreditCard } from "lucide-react";

export const Transactions = () => {
  const { merchantId } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [actionNote, setActionNote] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const loadOrders = async () => {
    if (!merchantId) return;
    setLoading(true);
    try {
      const data = await orderService.getOrders(merchantId);
      setOrders(data);
    } catch (err) {
      console.error("Failed to load transactions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, [merchantId]);

  const handleApproveAction = async (orderId, action) => {
    setActionLoading(true);
    try {
      await orderService.approveOrder(orderId, action, actionNote);
      setActionNote("");
      setSelectedOrder(null);
      await loadOrders();
    } catch (err) {
      console.error("Failed approval action:", err);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading merchant transaction records..." />;
  }

  const filteredOrders = orders.filter((o) => {
    if (statusFilter === "ALL") return true;
    return o.status === statusFilter || o.policy_status === statusFilter;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center space-x-2">
            <Receipt className="w-6 h-6 text-brand-400" />
            <span>Transaction Management</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Order lifecycle, Policy Engine outcomes, approval reviews, and payment history
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <Card className="!p-4">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium mr-2 flex items-center">
            <Filter className="w-3.5 h-3.5 mr-1" /> Filter Status:
          </span>
          {["ALL", "APPROVED", "AWAITING_APPROVAL", "BLOCKED", "PAID", "PAYMENT_FAILED", "CANCELLED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg border font-medium transition ${
                statusFilter === st
                  ? "bg-brand-600 text-white border-brand-500 shadow"
                  : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </Card>

      {/* Transactions Table */}
      <Card>
        {filteredOrders.length === 0 ? (
          <EmptyState
            icon={Receipt}
            title="No transaction records found"
            description="Use the AI Buyer Demo to initiate shopping orders."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-medium pb-2">
                  <th className="pb-3 font-medium">Order ID</th>
                  <th className="pb-3 font-medium">Customer</th>
                  <th className="pb-3 font-medium">Created At</th>
                  <th className="pb-3 font-medium">Total Amount</th>
                  <th className="pb-3 font-medium">Policy Outcome</th>
                  <th className="pb-3 font-medium">Order Status</th>
                  <th className="pb-3 font-medium text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredOrders.map((order) => (
                  <tr key={order.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3.5 font-mono text-brand-400 font-semibold">
                      #{order.id.slice(0, 8)}
                    </td>
                    <td className="py-3.5 text-slate-300 font-medium">
                      {order.customer_identifier || "Anonymous"}
                    </td>
                    <td className="py-3.5 text-slate-400">
                      {new Date(order.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                    </td>
                    <td className="py-3.5 font-bold text-slate-100">
                      ₹{parseFloat(order.total).toFixed(2)}
                    </td>
                    <td className="py-3.5">
                      <Badge status={order.policy_status} />
                    </td>
                    <td className="py-3.5">
                      <Badge status={order.status} />
                    </td>
                    <td className="py-3.5 text-right">
                      <button
                        onClick={() => setSelectedOrder(order)}
                        className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md font-medium text-xs transition"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Transaction Detail Modal / Drawer */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-100">
                  Order Details #{selectedOrder.id.slice(0, 8)}
                </h3>
                <p className="text-xs text-slate-400">
                  Customer: {selectedOrder.customer_identifier}
                </p>
              </div>
              <button
                onClick={() => setSelectedOrder(null)}
                className="p-1 text-slate-400 hover:text-slate-200 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Status Summary Cards */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
                <span className="text-slate-400">Policy Evaluation:</span>
                <div className="mt-1">
                  <Badge status={selectedOrder.policy_status} />
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  {selectedOrder.policy_reason || "Evaluated by 8-rule deterministic policy engine"}
                </p>
              </div>

              <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
                <span className="text-slate-400">Order Lifecycle Status:</span>
                <div className="mt-1">
                  <Badge status={selectedOrder.status} />
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  Approval Status: {selectedOrder.approval_status}
                </p>
              </div>
            </div>

            {/* Line Items */}
            <div>
              <h4 className="text-xs font-semibold text-slate-300 mb-2">Order Line Items</h4>
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl divide-y divide-slate-800/60 text-xs">
                {selectedOrder.items?.map((item) => (
                  <div key={item.id} className="p-3 flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-200">{item.product_name}</p>
                      <p className="text-[11px] text-slate-500 font-mono">SKU: {item.product_sku}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-slate-300 font-medium">{item.quantity} × ₹{parseFloat(item.unit_price).toFixed(2)}</p>
                      <p className="font-bold text-slate-100">₹{parseFloat(item.subtotal).toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Approval Controls if AWAITING_APPROVAL */}
            {selectedOrder.status === "AWAITING_APPROVAL" && (
              <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl space-y-3">
                <div className="flex items-center space-x-2 text-amber-400 font-semibold text-xs">
                  <FileText className="w-4 h-4" />
                  <span>Merchant Review Action Required</span>
                </div>
                <input
                  type="text"
                  value={actionNote}
                  onChange={(e) => setActionNote(e.target.value)}
                  placeholder="Optional review note (e.g. Approved high value order)..."
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
                <div className="flex items-center justify-end space-x-3">
                  <button
                    disabled={actionLoading}
                    onClick={() => handleApproveAction(selectedOrder.id, "REJECT")}
                    className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium rounded-lg transition"
                  >
                    Reject Order
                  </button>
                  <button
                    disabled={actionLoading}
                    onClick={() => handleApproveAction(selectedOrder.id, "APPROVE")}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-lg transition"
                  >
                    Approve Order for Payment
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
