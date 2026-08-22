import React, { useEffect, useRef, useState } from "react";
import { useBuyer } from "../../context/BuyerContext";
import { agentService } from "../../services/agentService";
import { orderService } from "../../services/orderService";
import { paymentService } from "../../services/paymentService";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import {
  Bot,
  Send,
  ShoppingBag,
  Trash2,
  CheckCircle2,
  ShieldCheck,
  Zap,
  Sparkles,
  CreditCard,
  AlertTriangle,
  RefreshCw,
  Plus,
  Minus,
  Check,
} from "lucide-react";

// Dynamically load Razorpay Checkout Script
const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

export const BuyerChat = () => {
  const {
    merchantId,
    customerIdentifier,
    cart,
    cartSummary,
    createOrGetCart,
    addToCart,
    updateQuantity,
    removeItem,
    refreshCartSummary,
  } = useBuyer();

  const [messages, setMessages] = useState([
    {
      sender: "assistant",
      text: "Hello! I am your AI Shopping Assistant. How can I help you find products today?",
      products: [],
      steps: [],
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [thinking, setThinking] = useState(false);
  const [agentStep, setAgentStep] = useState("");
  const [checkoutModal, setCheckoutModal] = useState(false);
  const [checkoutResult, setCheckoutResult] = useState(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  // Ensure cart exists on load
  useEffect(() => {
    if (merchantId && !cart) {
      createOrGetCart();
    }
  }, [merchantId]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || !merchantId) return;

    // Append user message
    const userMsg = { sender: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage("");

    setThinking(true);
    setAgentStep("Searching catalog...");

    try {
      let currentCartId = cart?.id;
      if (!currentCartId) {
        const newCart = await createOrGetCart();
        currentCartId = newCart.id;
      }

      // Call AI Agent API
      const res = await agentService.chat({
        message: text,
        merchant_id: merchantId,
        customer_identifier: customerIdentifier,
        cart_id: currentCartId,
      });

      // Refresh cart
      await refreshCartSummary(currentCartId, merchantId);

      // Append assistant message
      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: res.response,
          products: res.suggested_products || [],
          steps: res.execution_trace?.map((t) => t.tool_name) || ["Catalog searched", "Cart updated"],
        },
      ]);
    } catch (err) {
      console.error("Agent chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: "I encountered an error processing your request. Please try again.",
          products: [],
          steps: ["Execution failed"],
        },
      ]);
    } finally {
      setThinking(false);
      setAgentStep("");
    }
  };

  // Perform Checkout
  const handleInitiateCheckout = async () => {
    if (!cart || !merchantId) return;
    setCheckoutModal(true);
    setCheckoutLoading(true);
    setCheckoutResult(null);

    try {
      const orderData = await orderService.checkoutCart(cart.id, merchantId);
      setCheckoutResult({ type: "ORDER_CREATED", order: orderData });

      if (orderData.status === "APPROVED") {
        // Create payment order
        const payConfig = await paymentService.createPaymentOrder(orderData.id, merchantId);
        setCheckoutResult({ type: "READY_FOR_PAYMENT", order: orderData, payConfig });
      }
    } catch (err) {
      console.error("Checkout validation error:", err);
      const detail = err.response?.data?.detail || "Checkout validation failed.";
      setCheckoutResult({ type: "ERROR", message: detail });
    } finally {
      setCheckoutLoading(false);
    }
  };

  // Launch Razorpay Checkout Modal
  const handleLaunchRazorpay = async () => {
    if (!checkoutResult?.payConfig) return;
    const { payConfig, order } = checkoutResult;

    const resLoaded = await loadRazorpayScript();
    if (!resLoaded) {
      alert("Razorpay SDK failed to load. Please check internet connection.");
      return;
    }

    const options = {
      key: payConfig.razorpay_key_id,
      amount: payConfig.amount,
      currency: payConfig.currency,
      name: "AgentCart Store",
      description: `Order #${order.id.slice(0, 8)}`,
      order_id: payConfig.razorpay_order_id,
      handler: async function (response) {
        setCheckoutLoading(true);
        try {
          // Send signature to backend for verification
          const verifiedPayment = await paymentService.verifyPayment(
            order.id,
            response.razorpay_payment_id,
            response.razorpay_order_id,
            response.razorpay_signature,
            merchantId
          );
          setCheckoutResult({ type: "PAYMENT_SUCCESS", payment: verifiedPayment, order });
          await refreshCartSummary(cart.id, merchantId);
        } catch (verErr) {
          console.error("Signature verification error:", verErr);
          setCheckoutResult({ type: "PAYMENT_FAILED", message: "Signature verification failed." });
        } finally {
          setCheckoutLoading(false);
        }
      },
      prefill: {
        email: "demo-buyer@agentcart.dev",
        contact: "9999999999",
      },
      theme: {
        color: "#0c8ce9",
      },
    };

    const rzp = new window.Razorpay(options);
    rzp.on("payment.failed", function (response) {
      setCheckoutResult({
        type: "PAYMENT_FAILED",
        order,
        message: response.error?.description || "Payment was rejected or cancelled.",
      });
    });
    rzp.open();
  };

  // Retry Failed Payment
  const handleRetryPayment = async () => {
    if (!checkoutResult?.order) return;
    setCheckoutLoading(true);
    try {
      const retryRes = await paymentService.retryPayment(checkoutResult.order.id, merchantId);
      if (retryRes.status === "RETRY_INITIATED" && retryRes.payment_order) {
        setCheckoutResult({
          type: "READY_FOR_PAYMENT",
          order: checkoutResult.order,
          payConfig: retryRes.payment_order,
        });
      } else {
        setCheckoutResult({
          type: "RETRY_BLOCKED",
          message: retryRes.reason || "Maximum retry limit reached.",
        });
      }
    } catch (err) {
      console.error("Retry failed:", err);
    } finally {
      setCheckoutLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col lg:flex-row gap-6">
      {/* Left Column: Conversational AI Shopping Assistant */}
      <div className="flex-1 flex flex-col bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-md">
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-800/80 bg-slate-900 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100">AI Commerce Shopping Agent</h2>
              <p className="text-[11px] text-emerald-400 font-medium">Online • Policy Governed</p>
            </div>
          </div>

          <div className="hidden sm:flex items-center space-x-2">
            <Badge status="ALLOW">₹3,000 Auto-Allow</Badge>
            <Badge status="ALLOW_WITH_APPROVAL">₹5,000 Max Cap</Badge>
          </div>
        </div>

        {/* Chat Messages Body */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-xl p-3.5 rounded-2xl text-xs leading-relaxed ${
                  msg.sender === "user"
                    ? "bg-brand-600 text-white rounded-br-none shadow-md shadow-brand-600/20"
                    : "bg-slate-950/80 border border-slate-800/90 text-slate-200 rounded-bl-none shadow-lg"
                }`}
              >
                {/* Agent Action Steps */}
                {msg.steps && msg.steps.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2 pb-2 border-b border-slate-800/60">
                    {msg.steps.map((st, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-semibold rounded-md flex items-center"
                      >
                        <Check className="w-3 h-3 mr-1" /> {st}
                      </span>
                    ))}
                  </div>
                )}

                <p className="whitespace-pre-line">{msg.text}</p>
              </div>

              {/* Inline Product Cards */}
              {msg.products && msg.products.length > 0 && (
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
                  {msg.products.map((prod) => (
                    <div
                      key={prod.id}
                      className="p-3 bg-slate-950/90 border border-slate-800 rounded-xl flex flex-col justify-between"
                    >
                      <div>
                        <span className="text-[10px] font-mono text-brand-400 font-semibold">{prod.sku}</span>
                        <h4 className="font-semibold text-slate-100 text-xs mt-0.5">{prod.name}</h4>
                        <p className="text-[11px] font-bold text-emerald-400 mt-1">₹{parseFloat(prod.price).toFixed(2)}</p>
                      </div>
                      <button
                        onClick={() => addToCart(prod.id, 1)}
                        className="mt-3 w-full py-1.5 bg-brand-600 hover:bg-brand-500 text-white font-medium text-xs rounded-lg transition flex items-center justify-center space-x-1"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add to Cart</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {thinking && (
            <div className="flex items-center space-x-2 text-xs text-brand-400 bg-brand-500/10 border border-brand-500/20 px-3 py-2 rounded-xl w-fit animate-pulse">
              <Sparkles className="w-4 h-4" />
              <span>{agentStep || "Thinking about your request..."}</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="px-4 py-2 bg-slate-950/40 border-t border-slate-800/60 flex items-center space-x-2 overflow-x-auto text-[11px]">
          <span className="text-slate-500 font-semibold shrink-0">Try Demo Prompts:</span>
          <button
            onClick={() => handleSendMessage("I need a programming keyboard under ₹3000.")}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg shrink-0 transition"
          >
            "Keyboard under ₹3000"
          </button>
          <button
            onClick={() => handleSendMessage("Add a mouse.")}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg shrink-0 transition"
          >
            "Add a mouse"
          </button>
          <button
            onClick={() => handleSendMessage("What accessories go with my keyboard?")}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg shrink-0 transition"
          >
            "Recommend accessories"
          </button>
        </div>

        {/* Input Bar */}
        <div className="p-3 border-t border-slate-800 bg-slate-900">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask AI agent to find products, recommend add-ons, or build cart..."
              className="flex-1 px-4 py-2.5 bg-slate-950/90 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
            <button
              type="submit"
              disabled={thinking || !inputMessage.trim()}
              className="p-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-xl shadow-lg shadow-brand-600/20 transition"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>

      {/* Right Column: Real-Time Cart & Policy Checkout Panel */}
      <div className="w-full lg:w-80 flex flex-col space-y-4">
        <Card title="Your Shopping Cart" subtitle="Authoritative server-side prices">
          {!cartSummary || !cartSummary.subtotal ? (
            <div className="p-6 text-center text-xs text-slate-400">
              <ShoppingBag className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p>Your cart is empty.</p>
              <p className="text-[11px] text-slate-500 mt-1">Ask the AI agent to search products!</p>
            </div>
          ) : (
            <div className="space-y-4 text-xs">
              {/* Items List */}
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {cart?.items?.map((item) => (
                  <div
                    key={item.id}
                    className="p-2.5 bg-slate-950/60 border border-slate-800/80 rounded-xl flex items-center justify-between"
                  >
                    <div>
                      <p className="font-semibold text-slate-200 truncate max-w-[130px]">{item.product_name}</p>
                      <p className="text-[10px] text-emerald-400 font-mono">₹{parseFloat(item.unit_price).toFixed(2)}</p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => updateQuantity(item.id, item.quantity - 1)}
                        className="p-1 text-slate-400 hover:text-slate-200 bg-slate-900 rounded"
                      >
                        <Minus className="w-3 h-3" />
                      </button>
                      <span className="font-bold text-slate-100 text-xs w-4 text-center">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.id, item.quantity + 1)}
                        className="p-1 text-slate-400 hover:text-slate-200 bg-slate-900 rounded"
                      >
                        <Plus className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => removeItem(item.id)}
                        className="p-1 text-rose-400 hover:text-rose-300 ml-1"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Server Calculated Totals */}
              <div className="pt-3 border-t border-slate-800/80 space-y-1.5">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Subtotal:</span>
                  <span className="font-mono text-slate-200">₹{parseFloat(cartSummary.subtotal).toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Discounts:</span>
                  <span className="font-mono text-emerald-400">-₹{parseFloat(cartSummary.discount_total).toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between font-bold text-slate-100 text-sm pt-2 border-t border-slate-800/60">
                  <span>Total Amount:</span>
                  <span className="font-mono text-emerald-400 text-base">
                    ₹{parseFloat(cartSummary.total).toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Checkout Button */}
              <button
                onClick={handleInitiateCheckout}
                disabled={!cart?.items?.length}
                className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-600/25 transition flex items-center justify-center space-x-2 mt-2"
              >
                <CreditCard className="w-4 h-4" />
                <span>Policy Checkout</span>
              </button>
            </div>
          )}
        </Card>
      </div>

      {/* Checkout Governance Modal */}
      {checkoutModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-slate-100">Policy Engine Checkout</h3>
              </div>
              <button onClick={() => setCheckoutModal(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>

            {checkoutLoading ? (
              <LoadingSpinner text="Evaluating Policy Engine rules & preparing payment order..." />
            ) : checkoutResult?.type === "READY_FOR_PAYMENT" ? (
              <div className="space-y-4 text-xs">
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400 font-medium flex items-center space-x-2">
                  <CheckCircle2 className="w-5 h-5 shrink-0" />
                  <div>
                    <p className="font-bold">Policy Verdict: READY FOR PAYMENT</p>
                    <p className="text-[11px] text-slate-300">Transaction validated against spending limits.</p>
                  </div>
                </div>

                <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex justify-between text-slate-400">
                    <span>Order ID:</span>
                    <span className="font-mono text-slate-200">#{checkoutResult.order.id.slice(0, 8)}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Razorpay Order ID:</span>
                    <span className="font-mono text-brand-400">{checkoutResult.payConfig.razorpay_order_id}</span>
                  </div>
                  <div className="flex justify-between font-bold text-slate-100 text-sm pt-2 border-t border-slate-800">
                    <span>Payable Amount:</span>
                    <span className="text-emerald-400 font-mono">₹{parseFloat(checkoutResult.order.total).toFixed(2)}</span>
                  </div>
                </div>

                <button
                  onClick={handleLaunchRazorpay}
                  className="w-full py-3 bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-brand-600/25 transition flex items-center justify-center space-x-2"
                >
                  <CreditCard className="w-4 h-4" />
                  <span>Launch Razorpay Test Checkout</span>
                </button>
              </div>
            ) : checkoutResult?.type === "PAYMENT_SUCCESS" ? (
              <div className="space-y-4 text-xs text-center p-4">
                <div className="w-12 h-12 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto border border-emerald-500/20">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h4 className="text-lg font-bold text-slate-100">Payment Successful!</h4>
                <p className="text-slate-400">
                  Server signature verification completed cleanly. Internal order status set to <strong>PAID</strong>.
                </p>
                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 text-left font-mono text-[11px] space-y-1">
                  <p>Order ID: {checkoutResult.order?.id}</p>
                  <p>Payment Status: CAPTURED</p>
                </div>
                <button
                  onClick={() => setCheckoutModal(false)}
                  className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium rounded-xl transition"
                >
                  Done
                </button>
              </div>
            ) : checkoutResult?.type === "PAYMENT_FAILED" ? (
              <div className="space-y-4 text-xs p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl">
                <div className="flex items-center space-x-2 text-rose-400 font-bold text-sm">
                  <AlertTriangle className="w-5 h-5" />
                  <span>Payment Unsuccessful</span>
                </div>
                <p className="text-slate-300">
                  No duplicate charge made. Your order status is preserved as <strong>PAYMENT_FAILED</strong>.
                </p>
                <button
                  onClick={handleRetryPayment}
                  className="w-full py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl transition flex items-center justify-center space-x-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry Payment</span>
                </button>
              </div>
            ) : checkoutResult?.type === "ERROR" ? (
              <div className="space-y-4 text-xs p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400">
                <div className="flex items-center space-x-2 font-bold text-sm">
                  <AlertTriangle className="w-5 h-5" />
                  <span>Policy Check Failed / Blocked</span>
                </div>
                <p className="text-slate-300">{checkoutResult.message}</p>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
