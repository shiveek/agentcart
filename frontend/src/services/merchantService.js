import api from "./api";

export const merchantService = {
  async getMerchants() {
    const response = await api.get("/api/merchants");
    return response.data;
  },

  async getMerchant(id) {
    const response = await api.get(`/api/merchants/${id}`);
    return response.data;
  },

  async getPolicy(merchantId) {
    const response = await api.get(`/api/merchants/${merchantId}/policy`);
    return response.data;
  },

  async updatePolicy(merchantId, policyData) {
    const response = await api.put(`/api/merchants/${merchantId}/policy`, policyData);
    return response.data;
  },

  async getRelationships(merchantId) {
    const response = await api.get(`/api/merchants/${merchantId}/relationships`);
    return response.data;
  },
};
