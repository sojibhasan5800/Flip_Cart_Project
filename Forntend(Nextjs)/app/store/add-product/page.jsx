'use client'
import { assets } from "@/assets/assets"
import Image from "next/image"
import { useState } from "react"
import toast from "react-hot-toast"
import AxiosInstance from "../../../api/AxiosInstance" 

// ────────────────────────────────────────────────
// Reuse the SAME ImageKit upload hook as CreateStore
// ────────────────────────────────────────────────
import { useImageKitUpload } from "../../../hooks/useImageKitUpload";

export default function StoreAddProduct() {
    const categories = [
        'Electronics', 'Clothing', 'Home & Kitchen', 'Beauty & Health',
        'Toys & Games', 'Sports & Outdoors', 'Books & Media',
        'Food & Drink', 'Hobbies & Crafts', 'Others'
    ]

    // State for uploaded ImageKit URLs (what we send to backend)
    const [imageUrls, setImageUrls] = useState({
        1: null, // main image
        2: null,
        3: null,
        4: null,
    })

    // State for local previews (instant feedback before upload finishes)
    const [previews, setPreviews] = useState({
        1: null,
        2: null,
        3: null,
        4: null,
    })

    // Form data
    const [productInfo, setProductInfo] = useState({
        name: "",
        description: "",
        mrp: "",
        price: "",
        category: "",
        stock: "0",
    })

    const [loading, setLoading] = useState(false)

    // ────────────────────────────────────────────────
    // Same upload hook used in CreateStore
    // ────────────────────────────────────────────────
    const { uploadFile, loading: uploadLoading, error: uploadError, progress } = useImageKitUpload();

    const onChangeHandler = (e) => {
        const { name, value } = e.target;

    if (name === "stock") {
        // শুধু non-negative number allow করো
        if (value === "" || (/^\d+$/.test(value) && Number(value) >= 0)) {
            setProductInfo({ ...productInfo, [name]: value });
        }
        // negative বা invalid হলে ignore করবে (কোনো toast না দিয়ে silent)
        return;
    }
        setProductInfo({ ...productInfo, [e.target.name]: e.target.value })
    }

    // ────────────────────────────────────────────────
    // Handle image selection → show preview → upload to ImageKit → save URL
    // ────────────────────────────────────────────────
    const handleImageSelect = async (key, file) => {
        if (!file) return;

        // 1. Show instant local preview
        const previewUrl = URL.createObjectURL(file);
        setPreviews(prev => ({ ...prev, [key]: previewUrl }));

        try {
            // 2. Upload directly to ImageKit (same logic as CreateStore)
            const uploadedUrl = await uploadFile(file, {
                folder: '/products/',
                tags: ['product', `name-${productInfo.name || 'new'}`],
            });

            if (uploadError) throw new Error(uploadError);

            // 3. Save the final secure ImageKit URL
            setImageUrls(prev => ({ ...prev, [key]: uploadedUrl }));

            toast.success(`Image ${key} uploaded (${progress}%)`);

        } catch (err) {
            toast.error(`Image ${key} upload failed: ${err.message}`);
            setPreviews(prev => ({ ...prev, [key]: null }));
        }
    };

    const onSubmitHandler = async (e) => {
        e.preventDefault();

        // Validation: at least main image required
        if (!imageUrls[1]) {
            return toast.error("Please upload at least the main product image");
        }

        // Basic form validation
        if (!productInfo.name.trim()) return toast.error("Product name is required");
        if (!productInfo.description.trim()) return toast.error("Description is required");
        if (!productInfo.category) return toast.error("Please select a category");
        if (!productInfo.mrp || !productInfo.price) {
            return toast.error("MRP and Offer Price are required");
        }
        if (Number(productInfo.price) >= Number(productInfo.mrp)) {
            return toast.error("Offer price must be less than MRP");
        }
        if (!productInfo.stock || isNaN(Number(productInfo.stock)) || Number(productInfo.stock) < 0) {
            return toast.error("Please enter a valid stock quantity (0 or more)");
        }

        setLoading(true);

        try {
            const payload = {
                organization_id: localStorage.getItem("ACTIVE_ORG_ID"),
                // business_email: localStorage.getItem("ACTIVE_BUSINESS_EMAIL"),
                product_name: productInfo.name.trim(),
                description: productInfo.description.trim(),
                mrp: Number(productInfo.mrp),
                price: Number(productInfo.price),
                category: productInfo.category,
                stock: Number(productInfo.stock),

                // ────────────────────────────────────────────────
                // Send URLs only (same pattern as CreateStore)
                // ────────────────────────────────────────────────
                main_image_url: imageUrls[1],
                gallery_image_urls: [
                    imageUrls[2],
                    imageUrls[3],
                    imageUrls[4]
                ].filter(Boolean), // remove empty/null values
            };
            console.log(payload);
            const { data } = await AxiosInstance.post(
                "/api/store/products/",
                payload,{ useTenant: true }
            );

            toast.success(data.message || "Product added successfully!");

            // Reset form
            setProductInfo({
                name: "", description: "", mrp: "", price: "", category: "",
            });
            setImageUrls({ 1: null, 2: null, 3: null, 4: null });
            setPreviews({ 1: null, 2: null, 3: null, 4: null });

        } catch (error) {
            const errMsg = error?.response?.data?.error ||
                          error?.message ||
                          "Failed to add product. Please try again.";
            toast.error(errMsg);
            console.error("Product add error:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form 
            onSubmit={onSubmitHandler}
            className="text-slate-500 mb-28 px-4 md:px-8 max-w-5xl mx-auto"
        >
            <h1 className="text-2xl md:text-3xl font-semibold mb-2">
                Add New <span className="text-slate-800">Product</span>
            </h1>
            <p className="text-slate-600 mb-8">
                Fill in the details and upload images to list your product.
            </p>

            {/* Images Upload Section */}
            <div className="mb-8">
                <p className="font-medium mb-3">Product Images (Main + Gallery)</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map(key => (
                        <label 
                            key={key} 
                            htmlFor={`img${key}`} 
                            className="cursor-pointer group relative"
                        >
                            <div className="border-2 border-dashed border-slate-300 rounded-lg overflow-hidden hover:border-slate-500 transition">
                                <Image
                                    width={300}
                                    height={300}
                                    className="w-full h-40 object-cover"
                                    src={previews[key] || assets.upload_area}
                                    alt={`Product preview ${key}`}
                                />
                                {/* Upload overlay when in progress */}
                                {uploadLoading && previews[key] && (
                                    <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center text-white text-sm">
                                        <div>Uploading...</div>
                                        <div>{progress}%</div>
                                    </div>
                                )}
                                {/* Uploaded badge */}
                                {imageUrls[key] && (
                                    <div className="absolute bottom-2 right-2 bg-green-600 text-white text-xs px-2 py-1 rounded-full shadow">
                                        Uploaded
                                    </div>
                                )}
                            </div>
                            <input
                                type="file"
                                accept="image/*"
                                id={`img${key}`}
                                onChange={(e) => {
                                    if (e.target.files?.[0]) {
                                        handleImageSelect(key, e.target.files[0]);
                                    }
                                }}
                                hidden
                            />
                            <p className="text-xs text-center mt-1 text-slate-500">
                                {key === 1 ? 'Main Image*' : `Gallery ${key-1}`}
                            </p>
                        </label>
                    ))}
                </div>
            </div>

            {/* Form Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label className="block mb-2 font-medium">Product Name *</label>
                    <input
                        type="text"
                        name="name"
                        value={productInfo.name}
                        onChange={onChangeHandler}
                        placeholder="e.g. Premium Cotton T-Shirt"
                        className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500"
                        required
                    />
                </div>

                <div>
                    <label className="block mb-2 font-medium">Category *</label>
                    <select
                        name="category"
                        value={productInfo.category}
                        onChange={onChangeHandler}
                        className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500"
                        required
                    >
                        <option value="">Select Category</option>
                        {categories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block mb-2 font-medium">Actual Price (MRP) *</label>
                    <input
                        type="number"
                        name="mrp"
                        value={productInfo.mrp}
                        onChange={onChangeHandler}
                        placeholder="1200"
                        className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500"
                        required
                        min="1"
                    />
                </div>

                <div>
                    <label className="block mb-2 font-medium">Offer Price *</label>
                    <input
                        type="number"
                        name="price"
                        value={productInfo.price}
                        onChange={onChangeHandler}
                        placeholder="899"
                        className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500"
                        required
                        min="1"
                    />
                </div>
                <div>
                    <label className="block mb-2 font-medium">
                        Initial Stock *
                        <span className="text-xs text-slate-500 ml-2 font-normal">(items available to sell)</span>
                    </label>
                    <input
                        type="number"
                        name="stock"
                        value={productInfo.stock}
                        onChange={onChangeHandler}
                        placeholder="e.g. 100"
                        className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500"
                        required
                        min="0"
                        step="1"
                    />
                </div>
                
            </div>

            <div className="mt-6">
                <label className="block mb-2 font-medium">Description *</label>
                <textarea
                    name="description"
                    value={productInfo.description}
                    onChange={onChangeHandler}
                    rows={5}
                    placeholder="Detailed product description, features, specifications..."
                    className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500 resize-none"
                    required
                />
            </div>

            <button
                type="submit"
                disabled={loading || uploadLoading}
                className={`mt-10 px-10 py-3 rounded-lg text-white font-medium transition
                    ${loading || uploadLoading 
                        ? 'bg-slate-500 cursor-not-allowed' 
                        : 'bg-slate-800 hover:bg-slate-900 active:scale-95'}`}
            >
                {loading || uploadLoading ? (
                    <span className="flex items-center gap-2">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        </svg>
                        Processing...
                    </span>
                ) : (
                    "Add Product"
                )}
            </button>
        </form>
    )
}