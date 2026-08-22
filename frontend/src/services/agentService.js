import api from "./api";

export const agentService = {
  async chat({ message, merchant_id, customer_identifier, cart_id = null }) {
    const response = await api.post("/api/agent/chat", {
      message,
      merchant_id,
      customer_identifier,
      cart_id,
    });
    return response.data;
  },
};
