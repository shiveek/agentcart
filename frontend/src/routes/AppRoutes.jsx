import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "../components/layout/Layout";
import { Login } from "../pages/auth/Login";
import { Register } from "../pages/auth/Register";
import { Dashboard } from "../pages/merchant/Dashboard";
import { Products } from "../pages/merchant/Products";
import { Opportunities } from "../pages/merchant/Opportunities";
import { Policies } from "../pages/merchant/Policies";
import { Transactions } from "../pages/merchant/Transactions";
import { AuditTrail } from "../pages/merchant/AuditTrail";
import { BuyerChat } from "../pages/buyer/BuyerChat";
import { useAuth } from "../context/AuthContext";

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
};

export const AppRoutes = () => {
  return (
    <Routes>
      {/* Auth Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Merchant Governance Routes */}
      <Route
        path="/merchant"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/merchant/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="products" element={<Products />} />
        <Route path="opportunities" element={<Opportunities />} />
        <Route path="policies" element={<Policies />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="audit" element={<AuditTrail />} />
      </Route>

      {/* Buyer AI Shopping Demo Route */}
      <Route path="/buyer" element={<Layout />}>
        <Route index element={<BuyerChat />} />
      </Route>

      {/* Default Fallback */}
      <Route path="*" element={<Navigate to="/merchant/dashboard" replace />} />
    </Routes>
  );
};
