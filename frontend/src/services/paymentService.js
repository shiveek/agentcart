import api from "./api";

export const paymentService = {
  async createPaymentOrder(orderId, merchantId) {
    const response = await api.post(`/api/payments/orders/${orderId}`, {}, {
      headers: { "X-Merchant-ID": merchantId }
    });
    return response.data;
  },

  async verifyPayment(internalOrderId, razorpayPaymentId, razorpayOrderId, razorpaySignature, merchantId) {
    const response = await api.post("/api/payments/verify", {
      internal_order_id: internalOrderId,
      razorpay_payment_id: razorpayPaymentId,
      razorpay_order_id: razorpayOrderId,
      razorpay_signature: razorpaySignature,
    }, {
      headers: { "X-Merchant-ID": merchantId }
    });
    return response.data;
  },

  async getPayment(paymentId, merchantId) {
    const response = await api.get(`/api/payments/${paymentId}`, {
      headers: { "X-Merchant-ID": merchantId }
    });
    return response.data;
  },

  async retryPayment(orderId, merchantId) {
    const response = await api.post(`/api/payments/orders/${orderId}/retry`, {}, {
      headers: { "X-Merchant-ID": merchantId }
    });
    return response.data;
  },
};
