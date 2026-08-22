import api from "./api";

export const cartService = {
  async createCart(merchantId, customerIdentifier) {
    const response = await api.post(
      `/api/carts`,
      { customer_identifier: customerIdentifier },
      { headers: { "X-Merchant-ID": merchantId } }
    );
    return response.data;
  },

  async addCartItem(cartId, merchantId, productId, quantity) {
    const response = await api.post(
      `/api/carts/${cartId}/items`,
      { product_id: productId, quantity },
      { headers: { "X-Merchant-ID": merchantId } }
    );
    return response.data;
  },

  async getCart(cartId, merchantId) {
    const response = await api.get(`/api/carts/${cartId}`, {
      headers: { "X-Merchant-ID": merchantId },
    });
    return response.data;
  },

  async getCartSummary(cartId, merchantId) {
    const response = await api.get(`/api/carts/${cartId}/summary`, {
      headers: { "X-Merchant-ID": merchantId },
    });
    return response.data;
  },

  async updateCartItem(cartId, itemId, merchantId, quantity) {
    const response = await api.put(
      `/api/carts/${cartId}/items/${itemId}`,
      { quantity },
      { headers: { "X-Merchant-ID": merchantId } }
    );
    return response.data;
  },

  async removeCartItem(cartId, itemId, merchantId) {
    const response = await api.delete(`/api/carts/${cartId}/items/${itemId}`, {
      headers: { "X-Merchant-ID": merchantId },
    });
    return response.data;
  },
};
