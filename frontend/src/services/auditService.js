import api from "./api";

export const auditService = {
  async getAuditLogs(merchantId, limit = 50) {
    const response = await api.get(`/api/orders/audit-logs`, {
      params: { limit },
      headers: { "X-Merchant-ID": merchantId },
    });
    return response.data;
  },
};
