import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { productService } from "../../services/productService";
import { Card } from "../../components/common/Card";
import { Badge } from "../../components/common/Badge";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { EmptyState } from "../../components/common/EmptyState";
import { Package, Search, Filter, Layers } from "lucide-react";

export const Products = () => {
  const { merchantId } = useAuth();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [inStockOnly, setInStockOnly] = useState(false);

  useEffect(() => {
    const loadProducts = async () => {
      if (!merchantId) return;
      setLoading(true);
      try {
        const data = await productService.getProducts(merchantId);
        setProducts(data);
      } catch (err) {
        console.error("Failed to load products:", err);
      } finally {
        setLoading(false);
      }
    };
    loadProducts();
  }, [merchantId]);

  if (loading) {
    return <LoadingSpinner text="Loading merchant product catalog..." />;
  }

  // Categories list
  const categories = ["ALL", ...new Set(products.map((p) => p.category).filter(Boolean))];

  // Filter products
  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === "ALL" || p.category === selectedCategory;
    const stockQty = p.inventory?.available_quantity || 0;
    const matchesStock = !inStockOnly || stockQty > 0;
    return matchesSearch && matchesCategory && matchesStock;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Product Catalog</h1>
          <p className="text-xs text-slate-400 mt-1">Manage AI-transactable SKUs, prices, and live stock levels</p>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-2 rounded-xl">
          <Package className="w-4 h-4 text-brand-400" />
          <span>Total Products: <strong className="text-slate-100">{products.length}</strong></span>
        </div>
      </div>

      {/* Filter Bar */}
      <Card className="!p-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search product name, SKU, or category..."
              className="w-full pl-9 pr-4 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
            />
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-slate-950/80 border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:border-brand-500"
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat === "ALL" ? "All Categories" : cat}
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={inStockOnly}
                onChange={(e) => setInStockOnly(e.target.checked)}
                className="rounded border-slate-800 bg-slate-950 text-brand-600 focus:ring-brand-500"
              />
              <span>In Stock Only</span>
            </label>
          </div>
        </div>
      </Card>

      {/* Products Table */}
      <Card>
        {filteredProducts.length === 0 ? (
          <EmptyState title="No matching products found" description="Try adjusting your search query or filters." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-medium pb-2">
                  <th className="pb-3 font-medium">SKU</th>
                  <th className="pb-3 font-medium">Product Name</th>
                  <th className="pb-3 font-medium">Category</th>
                  <th className="pb-3 font-medium">Price</th>
                  <th className="pb-3 font-medium">Available Quantity</th>
                  <th className="pb-3 font-medium">Stock Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredProducts.map((product) => {
                  const qty = product.inventory?.available_quantity || 0;
                  const inStock = qty > 0;
                  return (
                    <tr key={product.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3.5 font-mono text-brand-400 font-semibold">{product.sku}</td>
                      <td className="py-3.5">
                        <p className="font-semibold text-slate-100">{product.name}</p>
                        <p className="text-[11px] text-slate-400 max-w-xs truncate">{product.description}</p>
                      </td>
                      <td className="py-3.5 text-slate-300">
                        <span className="px-2 py-1 bg-slate-800/80 rounded-md border border-slate-700/50 font-medium">
                          {product.category || "General"}
                        </span>
                      </td>
                      <td className="py-3.5 font-bold text-slate-100">
                        ₹{parseFloat(product.price).toFixed(2)}
                      </td>
                      <td className="py-3.5 font-mono text-slate-300 font-medium">
                        {qty} units
                      </td>
                      <td className="py-3.5">
                        <Badge status={inStock ? "ACTIVE" : "FAILED"}>
                          {inStock ? "IN STOCK" : "OUT OF STOCK"}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
