import api from "./api";

export const productService = {
  async getProducts(merchantId, params = {}) {
    const response = await api.get(`/api/merchants/${merchantId}/products`, { params });
    return response.data;
  },

  async getProduct(productId) {
    const response = await api.get(`/api/products/${productId}`);
    return response.data;
  },

  async getCatalog(merchantId) {
    const response = await api.get(`/api/agent/catalog/${merchantId}`);
    return response.data;
  },
};
