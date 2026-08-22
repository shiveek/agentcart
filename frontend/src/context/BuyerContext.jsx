import React, { createContext, useContext, useEffect, useState } from "react";
import { cartService } from "../services/cartService";
import { merchantService } from "../services/merchantService";

const BuyerContext = createContext(null);

export const BuyerProvider = ({ children }) => {
  const [merchantId, setMerchantId] = useState(null);
  const [customerIdentifier] = useState("demo-buyer-001");
  const [cart, setCart] = useState(null);
  const [cartSummary, setCartSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  // Initialize active demo merchant
  useEffect(() => {
    const fetchMerchant = async () => {
      try {
        const merchants = await merchantService.getMerchants();
        if (merchants && merchants.length > 0) {
          setMerchantId(merchants[0].id);
        }
      } catch (err) {
        console.error("Failed to load demo merchant:", err);
      }
    };
    fetchMerchant();
  }, []);

  const refreshCartSummary = async (cartId, mId) => {
    try {
      const summary = await cartService.getCartSummary(cartId, mId || merchantId);
      const cartData = await cartService.getCart(cartId, mId || merchantId);
      setCartSummary(summary);
      setCart(cartData);
    } catch (err) {
      console.error("Failed to refresh cart:", err);
    }
  };

  const createOrGetCart = async (overrideMerchantId = null) => {
    const targetMerchantId = overrideMerchantId || merchantId;
    if (!targetMerchantId) return null;

    setLoading(true);
    try {
      const newCart = await cartService.createCart(targetMerchantId, customerIdentifier);
      setCart(newCart);
      await refreshCartSummary(newCart.id, targetMerchantId);
      setLoading(false);
      return newCart;
    } catch (err) {
      console.error("Error creating cart:", err);
      setLoading(false);
      throw err;
    }
  };

  const addToCart = async (productId, quantity = 1) => {
    let currentCart = cart;
    if (!currentCart) {
      currentCart = await createOrGetCart();
    }
    setLoading(true);
    try {
      await cartService.addCartItem(currentCart.id, merchantId, productId, quantity);
      await refreshCartSummary(currentCart.id, merchantId);
      setLoading(false);
    } catch (err) {
      setLoading(false);
      throw err;
    }
  };

  const updateQuantity = async (itemId, quantity) => {
    if (!cart) return;
    setLoading(true);
    try {
      if (quantity <= 0) {
        await cartService.removeCartItem(cart.id, itemId, merchantId);
      } else {
        await cartService.updateCartItem(cart.id, itemId, merchantId, quantity);
      }
      await refreshCartSummary(cart.id, merchantId);
      setLoading(false);
    } catch (err) {
      setLoading(false);
      throw err;
    }
  };

  const removeItem = async (itemId) => {
    if (!cart) return;
    setLoading(true);
    try {
      await cartService.removeCartItem(cart.id, itemId, merchantId);
      await refreshCartSummary(cart.id, merchantId);
      setLoading(false);
    } catch (err) {
      setLoading(false);
      throw err;
    }
  };

  return (
    <BuyerContext.Provider
      value={{
        merchantId,
        setMerchantId,
        customerIdentifier,
        cart,
        cartSummary,
        loading,
        createOrGetCart,
        addToCart,
        updateQuantity,
        removeItem,
        refreshCartSummary,
      }}
    >
      {children}
    </BuyerContext.Provider>
  );
};

export const useBuyer = () => {
  const context = useContext(BuyerContext);
  if (!context) {
    throw new Error("useBuyer must be used within a BuyerProvider");
  }
  return context;
};
