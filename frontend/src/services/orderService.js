import api from "./api";

export const orderService = {
  async checkoutCart(cartId, merchantId, idempotencyKey = null) {
    const headers = { "X-Merchant-ID": merchantId };
    if (idempotencyKey) {
      headers["Idempotency-Key"] = idempotencyKey;
    }
    const response = await api.post(`/api/orders/from-cart/${cartId}`, {}, { headers });
    return response.data;
  },

  async getOrders(merchantId) {
    const response = await api.get(`/api/orders`, {
      headers: { "X-Merchant-ID": merchantId },
    });
    return response.data;
  },

  async getOrder(orderId, merchantId) {
    const response = await api.get(`/api/orders/${orderId}`, {
      headers: { "X-Merchant-ID": merchantId },
    });
    return response.data;
  },

  async approveOrder(orderId, action, note = "") {
    const response = await api.post(`/api/orders/${orderId}/approve`, { action, note });
    return response.data;
  },
};
