// app/(public)/shop/page.jsx
'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import ProductCard from "@/components/ProductCard"
import Loading from "@/components/Loading"
import AxiosInstance from '@/api/AxiosInstance'

export default function Shop() {
  const searchParams = useSearchParams()
  const search = searchParams.get('search')

  const [products, setProducts] = useState([])
  const [nextCursor, setNextCursor] = useState(null)
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [error, setError] = useState(null)

  const loader = useRef(null)

  const loadProducts = useCallback(async (cursor = null) => {
    if (loading || !hasMore) return;
    setLoading(true);
    setError(null);

    try {
      const params = cursor ? { cursor } : {};
      const response = await AxiosInstance.get(
        'api/public_data/all-shop-products/',
        { params }
      );

      const newProducts = response.data.results || response.data || [];
      const newCursor = response.data.next_cursor || null;

      // IMPORTANT: check duplicates before adding
      setProducts(prev => {
        const existingIds = new Set(prev.map(p => p.id));
        const uniqueNew = newProducts.filter(p => !existingIds.has(p.id));

        if (uniqueNew.length === 0) {
          // If no new products are received, stop further loading
          setHasMore(false);
          return prev;
        }

        return [...prev, ...uniqueNew];
      });

      setNextCursor(newCursor);

      // If no cursor or no new products → end of list
      if (!newCursor || newProducts.length === 0) {
        setHasMore(false);
      }

    } catch (err) {
      console.error("Shop products load error:", err);
      setError("Failed to load products.");
    } finally {
      setLoading(false);
    }
  }, [loading, hasMore]);

  // Initial load
  useEffect(() => {
    loadProducts()
  }, [])

  // Infinite scroll – Intersection Observer
  useEffect(() => {
    const options = { root: null, rootMargin: '200px', threshold: 0.1 }

    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasMore && !loading) {
        loadProducts(nextCursor)
      }
    }, options)

    if (loader.current) {
      observer.observe(loader.current)
    }

    return () => {
      if (loader.current) {
        observer.unobserve(loader.current)
      }
    }
  }, [nextCursor, hasMore, loading, loadProducts])

  // Search filter (frontend only) – can be moved to backend if needed
  const filteredProducts = search
    ? products.filter(product =>
        (product.product_name || '').toLowerCase().includes(search.toLowerCase()) ||
        (product.description || '').toLowerCase().includes(search.toLowerCase())
      )
    : products

  return (
    <div className="min-h-[80vh] mx-4 sm:mx-6 lg:mx-auto max-w-7xl py-8">
      <h1 className="text-2xl sm:text-3xl font-semibold mb-6 md:mb-8">
        {search ? `Search results for "${search}"` : 'All Products'}
      </h1>

      {error && (
        <p className="text-red-600 text-center my-6">{error}</p>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6">
        {filteredProducts.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>

      {/* Loader and last item reference */}
      <div ref={loader} className="col-span-full py-10 flex justify-center">
        {loading && <Loading />}
        {!hasMore && products.length > 0 && !loading && (
          <p className="text-gray-500 text-center">
            All products have been loaded
          </p>
        )}
      </div>

      {filteredProducts.length === 0 && !loading && (
        <p className="text-center text-gray-600 mt-12 text-lg">
          No products found
        </p>
      )}
    </div>
  )
}