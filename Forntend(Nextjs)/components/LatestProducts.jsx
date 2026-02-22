'use client'
import React, { useEffect, useState } from 'react'
import Title from './Title'
import ProductCard from './ProductCard'
import AxiosInstance from '../api/AxiosInstance'

const LatestProducts = () => {
    const displayQuantity = 4
    const [products, setProducts] = useState([])

    useEffect(() => {
        const fetchProducts = async () => {
            try {
                const res = await AxiosInstance.get('api/public_data/latest-products/')
                setProducts(res.data)
            } catch (err) {
                console.error("Failed to fetch latest products:", err)
            }
        }

        fetchProducts()
    }, [])

    if (!products.length) return null

    return (
        <div className='px-6 my-30 max-w-6xl mx-auto'>
            <Title 
                title='Latest Products' 
                description={`Showing ${products.length < displayQuantity ? products.length : displayQuantity} of ${products.length} products`} 
                href='/shop' 
            />
            <div className='mt-12 grid grid-cols-2 sm:flex flex-wrap gap-6 justify-between'>
                {products
                    .slice(0, displayQuantity)
                    .map((product, index) => (
                        <ProductCard key={index} product={product} />
                ))}
            </div>
        </div>
    )
}

export default LatestProducts