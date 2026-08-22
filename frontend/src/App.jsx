import React from "react";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { BuyerProvider } from "./context/BuyerContext";
import { AppRoutes } from "./routes/AppRoutes";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <BuyerProvider>
          <AppRoutes />
        </BuyerProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
