// 

'use client'
import { useEffect, useState } from "react"
import { format, formatDistanceToNow } from "date-fns"
import toast from "react-hot-toast"
import { DeleteIcon, ToggleLeft, ToggleRight, Clock, AlertCircle,Edit } from "lucide-react"
import AxiosInstance from '../../../api/AxiosInstance'
import useUser from '../../../hooks/useUser'

export default function AdminCoupons() {
    const { user,isSuperAdmin } = useUser()
    const [coupons, setCoupons] = useState([])
    const [loading, setLoading] = useState(false)
    const [stats, setStats] = useState({
        total: 0, active: 0, expired: 0, upcoming: 0, inactive: 0
    })
    const [currentStatus, setCurrentStatus] = useState(null)

    const [organizations, setOrganizations] = useState([])
    const [editingCoupon, setEditingCoupon] = useState(null)
    const [organizationsMap, setOrganizationsMap] = useState({})
    const [newCoupon, setNewCoupon] = useState({
        code: '',
        description: '',
        discount: '',
        forNewUser: false,
        forMember: false,
        isPublic: false,
        validFrom: new Date().toISOString().split('T')[0],
        validTo: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days from now
        usageLimit: 100,
        minOrderValue: 0,
        organization: ''
    })

    const [editForm, setEditForm] = useState({
        description: '',
        discount: '',
        validFrom: '',
        validTo: '',
        usageLimit: '',
        minOrderValue: '',
        forNewUser: false,
        forMember: false,
        isPublic: false,
        organization: ''   // super admin এর জন্য
    })

    const fetchCoupons = async (status = null) => {
        setLoading(true)
        try {
            const params = status ? { status } : {}
            const { data } = await AxiosInstance.get(
                'api/admin_core/coupons/',
                { params }
            )
            setCoupons(data)
            setCurrentStatus(status)
        } catch (error) {
            console.error("Error fetching coupons:", error)
            toast.error("Failed to load coupons")
        } finally {
            setLoading(false)
        }
    }

    // ← নতুন: এডিট মোডে কুপন লোড করা
    const startEditCoupon = (coupon) => {
        setEditingCoupon(coupon)
        setEditForm({
            description: coupon.description || '',
            discount: coupon.discount || '',
            validFrom: new Date(coupon.valid_from).toISOString().split('T')[0],
            validTo: new Date(coupon.valid_to).toISOString().split('T')[0],
            usageLimit: coupon.usage_limit || 100,
            minOrderValue: coupon.min_order_value || 0,
            forNewUser: coupon.for_new_user || false,
            forMember: coupon.for_member || false,
            isPublic: coupon.is_public || false,
            organization: coupon.organization || ''
        })
    }


    const fetchStats = async () => {
        try {
            const { data } = await AxiosInstance.get('api/admin_core/coupons/stats/')
            console.log("Stats fetched successfully")

            setStats(data)
        } catch (error) {
            console.error("Error fetching stats:", error)
        }
    }

    const handleAddCoupon = async (e) => {
        e.preventDefault()
        
        // Validate discount
        const discount = Number(newCoupon.discount)
        if (discount <= 0 || discount > 100) {
            toast.error("Discount must be between 1 and 100 percent")
            return
        }
        
        // Prepare payload
        const payload = {
            code: newCoupon.code.toUpperCase(),
            description: newCoupon.description,
            discount: discount,
            for_new_user: newCoupon.forNewUser,
            for_member: newCoupon.forMember,
            is_public: newCoupon.isPublic,
            valid_from: new Date(newCoupon.validFrom + 'T00:00:00').toISOString(),
            valid_to: new Date(newCoupon.validTo + 'T23:59:59').toISOString(),
            usage_limit: Number(newCoupon.usageLimit) || 100,
            min_order_value: Number(newCoupon.minOrderValue) || 0,
            organization: newCoupon.organization || null
        }
        // console.log("Sending payload to backend:", payload)
        
        try {
            await toast.promise(
                AxiosInstance.post('api/admin_core/coupons/', payload),
                {
                    loading: "Creating coupon...",
                    success: (res) => {
                        resetForm()
                        fetchCoupons()
                        fetchStats()
                        return "Coupon created successfully!"
                    },
                    error: (err) => {
                        return err.response?.data?.code?.[0] || 
                               err.response?.data?.valid_to?.[0] || 
                               "Failed to create coupon"
                    }
                }
            )
        } catch (error) {
            console.error("Coupon creation error:", error)
        }
    }

    // ← নতুন: এডিট ফর্ম সাবমিট
    const handleUpdateCoupon = async (e) => {
        e.preventDefault()

        if (!editingCoupon) return

        const discount = Number(editForm.discount)
        if (discount <= 0 || discount > 100) {
            toast.error("Discount must be between 1 and 100")
            return
        }

        const payload = {
            description: editForm.description,
            discount: discount,
            valid_from: new Date(editForm.validFrom + 'T00:00:00').toISOString(),
            valid_to: new Date(editForm.validTo + 'T23:59:59').toISOString(),
            usage_limit: Number(editForm.usageLimit) || 100,
            min_order_value: Number(editForm.minOrderValue) || 0,
            for_new_user: editForm.forNewUser,
            for_member: editForm.forMember,
            is_public: editForm.isPublic,
        }
    
        // Super admin হলে organization চেঞ্জ করতে দেওয়া যাবে
        if (isSuperAdmin && editForm.organization) {
            payload.organization = editForm.organization
        }

        try {
            await toast.promise(
                AxiosInstance.put(`api/admin_core/coupons/${editingCoupon.code}/`, payload),
                {
                    loading: "Updating coupon...",
                    success: () => {
                        setEditingCoupon(null)  // এডিট মোড বন্ধ
                        fetchCoupons(currentStatus)
                        fetchStats()
                        return "Coupon updated successfully!"
                    },
                    error: (err) => err.response?.data?.detail || "Failed to update coupon"
                }
            )
        } catch (error) {
            console.error("Update error:", error)
        }
    }

    const handleChange = (e) => {
        const { name, value, type } = e.target
        setNewCoupon(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? e.target.checked : value
        }))
    }

    // ← নতুন: এডিট ফর্ম চেঞ্জ হ্যান্ডলার
    const handleEditChange = (e) => {
        const { name, value, type, checked } = e.target
        setEditForm(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }))
    }

    const deleteCoupon = async (code) => {
        const confirm = window.confirm(`Are you sure you want to delete coupon "${code}"?`)
        if (!confirm) return
        
        try {
            await toast.promise(
                AxiosInstance.delete(`api/admin_core/coupons/${code}/`),
                {
                    loading: "Deleting coupon...",
                    success: () => {
                        fetchCoupons()
                        fetchStats()
                        return "Coupon deleted successfully!"
                    },
                    error: "Failed to delete coupon"
                }
            )
        } catch (error) {
            console.error("Delete error:", error)
        }
    }

    const toggleCouponStatus = async (coupon) => {
        const action = coupon.is_active ? 'deactivate' : 'activate'
        const url = `api/admin_core/coupons/${coupon.code}/${action}/`
        
        try {
            await toast.promise(
                AxiosInstance.post(url),
                {
                    loading: `${action === 'activate' ? 'Activating' : 'Deactivating'} coupon...`,
                    success: (res) => {
                        fetchCoupons()
                        fetchStats()
                        return res.data.message
                    },
                    error: (err) => err.response?.data?.message || "Operation failed"
                }
            )
        } catch (error) {
            console.error("Toggle error:", error)
        }
    }

    const resetForm = () => {
        setNewCoupon({
            code: '',
            description: '',
            discount: '',
            forNewUser: false,
            forMember: false,
            isPublic: false,
            validFrom: new Date().toISOString().split('T')[0],
            validTo: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            usageLimit: 100,
            minOrderValue: 0,
            organization: ''
        })
    }

    const getStatusBadge = (coupon) => {
        const now = new Date()
        const validFrom = new Date(coupon.valid_from)
        const validTo = new Date(coupon.valid_to)
        
        if (coupon.is_expired || validTo < now) {
            return <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">Expired</span>
        }
        if (!coupon.is_active) {
            return <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">Inactive</span>
        }
        if (validFrom > now) {
            return <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">Upcoming</span>
        }
        return <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">Active</span>
    }

    const getTimeRemaining = (validTo) => {
        const now = new Date()
        const expiry = new Date(validTo)
        
        if (expiry < now) return "Expired"
        
        const diffHours = Math.floor((expiry - now) / (1000 * 60 * 60))
        
        if (diffHours < 24) {
            return `${diffHours} hours remaining`
        } else {
            const diffDays = Math.floor(diffHours / 24)
            return `${diffDays} days remaining`
        }
    }

    // useEffect(() => {
    //     fetchCoupons()
    // }, [])

    useEffect(() => {
        if (!user) return

        if (isSuperAdmin) {
            const fetchStores = async () => {
                try {
                    const { data } = await AxiosInstance.get(
                        'api/admin_core/store-approval/?status=approved'
                    )
                    const orgs = data.data || []
                    setOrganizations(data.data || [])
                    // ← নতুন: id → business_name map তৈরি
                const map = {}
                orgs.forEach(org => {
                    map[org.id] = org.business_name
                })
                setOrganizationsMap(map)
                } catch {
                    toast.error("দোকানের লিস্ট লোড করা যায়নি")
                }
            }
            fetchStores()
        }

        fetchCoupons()   // initial list
        fetchStats()     // initial stats
    }, [user])

    return (
        <div className="text-slate-500 mb-40 p-4">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                <div className="bg-white p-4 rounded-lg shadow border">
                    <div className="text-2xl font-bold text-slate-800">{stats.total}</div>
                    <div className="text-sm text-slate-500">Total Coupons</div>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border border-green-200">
                    <div className="text-2xl font-bold text-green-600">{stats.active}</div>
                    <div className="text-sm text-slate-500">Active</div>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border border-red-200">
                    <div className="text-2xl font-bold text-red-600">{stats.expired}</div>
                    <div className="text-sm text-slate-500">Expired</div>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border border-blue-200">
                    <div className="text-2xl font-bold text-blue-600">{stats.upcoming}</div>
                    <div className="text-sm text-slate-500">Upcoming</div>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
                    <div className="text-2xl font-bold text-gray-600">{stats.inactive}</div>
                    <div className="text-sm text-slate-500">Inactive</div>
                </div>
            </div>

            {/* Add Coupon Form */}
            <form onSubmit={handleAddCoupon} className="bg-white p-6 rounded-lg shadow mb-8 max-w-2xl">
                <h2 className="text-2xl font-bold mb-4">Add New Coupon</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Coupon Code *</label>
                        <input 
                            type="text" 
                            placeholder="SUMMER50"
                            className="w-full p-2 border border-slate-300 rounded-md"
                            name="code" 
                            value={newCoupon.code}
                            onChange={handleChange}
                            required
                            pattern="[A-Z0-9]+"
                            title="Uppercase letters and numbers only"
                        />
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium mb-1">Discount (%) *</label>
                        <input 
                            type="number" 
                            min="1" 
                            max="100" 
                            step="0.01"
                            className="w-full p-2 border border-slate-300 rounded-md"
                            name="discount" 
                            value={newCoupon.discount}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    
                    <div className="md:col-span-2">
                        <label className="block text-sm font-medium mb-1">Description *</label>
                        <input 
                            type="text" 
                            placeholder="Summer sale discount"
                            className="w-full p-2 border border-slate-300 rounded-md"
                            name="description" 
                            value={newCoupon.description}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium mb-1">Valid From</label>
                        <input 
                            type="date" 
                            className="w-full p-2 border border-slate-300 rounded-md"
                            name="validFrom" 
                            value={newCoupon.validFrom}
                            onChange={handleChange}
                            min={new Date().toISOString().split('T')[0]}
                        />
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium mb-1">Valid To *</label>
                        <input 
                            type="date" 
                            className="w-full p-2 border border-slate-300 rounded-md"
                            name="validTo" 
                            value={newCoupon.validTo}
                            onChange={handleChange}
                            min={newCoupon.validFrom}
                            required
                        />
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium mb-1">Usage Limit</label>
                        <input 
                            type="number" 
                            min="1"
                            className="w-full p-2 border border-slate-300 rounded-md"
                            name="usageLimit" 
                            value={newCoupon.usageLimit}
                            onChange={handleChange}
                        />
                    </div>
                    
                    <div>
                        <label className="block text-sm font-medium mb-1">Minimum Order Value</label>
                        <input 
                            type="number" 
                            min="0"
                            step="0.01"
                            className="w-full p-2 border border-slate-300 rounded-md"
                            name="minOrderValue" 
                            value={newCoupon.minOrderValue}
                            onChange={handleChange}
                        />
                    </div>
                    {/* new code add */}

                    {isSuperAdmin && (
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium mb-1">
                                Select store for this coupon
                            </label>
                            <select
                                name="organization"
                                value={newCoupon.organization}
                                onChange={handleChange}
                                className="w-full p-2 border border-slate-300 rounded-md"
                            >
                                <option value="">All stores (Global)</option>
                                {organizations.map(org => (
                                    <option key={org.id} value={org.id}>
                                        {org.business_name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                
                
                </div>
                
                <div className="mt-4 space-y-3">
                    <div className="flex items-center">
                        <input 
                            type="checkbox" 
                            id="forNewUser"
                            className="mr-2 h-4 w-4"
                            checked={newCoupon.forNewUser}
                            onChange={(e) => setNewCoupon({...newCoupon, forNewUser: e.target.checked})}
                        />
                        <label htmlFor="forNewUser">For New Users Only</label>
                    </div>
                    
                    <div className="flex items-center">
                        <input 
                            type="checkbox" 
                            id="forMember"
                            className="mr-2 h-4 w-4"
                            checked={newCoupon.forMember}
                            onChange={(e) => setNewCoupon({...newCoupon, forMember: e.target.checked})}
                        />
                        <label htmlFor="forMember">For Members Only</label>
                    </div>
                    
                    <div className="flex items-center">
                        <input 
                            type="checkbox" 
                            id="isPublic"
                            className="mr-2 h-4 w-4"
                            checked={newCoupon.isPublic}
                            onChange={(e) => setNewCoupon({...newCoupon, isPublic: e.target.checked})}
                        />
                        <label htmlFor="isPublic">Public Coupon</label>
                    </div>
                </div>
                
                <button 
                    type="submit"
                    className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                >
                    Create Coupon
                </button>
            </form>



            {editingCoupon && (
                <form onSubmit={handleUpdateCoupon} className="bg-yellow-50 p-6 rounded-lg shadow mb-8 max-w-2xl border border-yellow-300">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-2xl font-bold">Edit Coupon: {editingCoupon.code}</h2>
                        <button 
                            type="button"
                            onClick={() => setEditingCoupon(null)}
                            className="text-red-600 hover:text-red-800"
                        >
                            Cancel Edit
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">Description</label>
                            <input 
                                type="text" 
                                name="description"
                                value={editForm.description}
                                onChange={handleEditChange}
                                className="w-full p-2 border rounded-md"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Discount (%)</label>
                            <input 
                                type="number" 
                                name="discount"
                                value={editForm.discount}
                                onChange={handleEditChange}
                                min="1" max="100" step="0.01"
                                className="w-full p-2 border rounded-md"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Valid From</label>
                            <input 
                                type="date" 
                                name="validFrom"
                                value={editForm.validFrom}
                                onChange={handleEditChange}
                                className="w-full p-2 border rounded-md"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Valid To</label>
                            <input 
                                type="date" 
                                name="validTo"
                                value={editForm.validTo}
                                onChange={handleEditChange}
                                className="w-full p-2 border rounded-md"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Usage Limit</label>
                            <input 
                                type="number" 
                                name="usageLimit"
                                value={editForm.usageLimit}
                                onChange={handleEditChange}
                                className="w-full p-2 border rounded-md"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Min Order Value</label>
                            <input 
                                type="number" 
                                name="minOrderValue"
                                value={editForm.minOrderValue}
                                onChange={handleEditChange}
                                step="0.01"
                                className="w-full p-2 border rounded-md"
                            />
                        </div>

                        {/* Super Admin এর জন্য Organization চেঞ্জ করার অপশন */}
                        {isSuperAdmin && (
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium mb-1">Change Store (Optional)</label>
                                <select
                                    name="organization"
                                    value={editForm.organization}
                                    onChange={handleEditChange}
                                    className="w-full p-2 border rounded-md"
                                >
                                    <option value="">Keep current store</option>
                                    {organizations.map(org => (
                                        <option key={org.id} value={org.id}>
                                            {org.business_name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {/* চেকবক্সগুলো */}
                        <div className="md:col-span-2 space-y-3">
                            <div className="flex items-center">
                                <input 
                                    type="checkbox" 
                                    id="edit-forNewUser"
                                    checked={editForm.forNewUser}
                                    onChange={(e) => setEditForm({...editForm, forNewUser: e.target.checked})}
                                    className="mr-2 h-4 w-4"
                                />
                                <label htmlFor="edit-forNewUser">For New Users Only</label>
                            </div>

                            <div className="flex items-center">
                                <input 
                                    type="checkbox" 
                                    id="edit-forMember"
                                    checked={editForm.forMember}
                                    onChange={(e) => setEditForm({...editForm, forMember: e.target.checked})}
                                    className="mr-2 h-4 w-4"
                                />
                                <label htmlFor="edit-forMember">For Members Only</label>
                            </div>

                            <div className="flex items-center">
                                <input 
                                    type="checkbox" 
                                    id="edit-isPublic"
                                    checked={editForm.isPublic}
                                    onChange={(e) => setEditForm({...editForm, isPublic: e.target.checked})}
                                    className="mr-2 h-4 w-4"
                                />
                                <label htmlFor="edit-isPublic">Public Coupon</label>
                            </div>
                        </div>
                    </div>

                    <button 
                        type="submit"
                        className="mt-6 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                    >
                        Save Changes
                    </button>
                </form>
            )}



            {/* Edit Form */}


            {/* Coupons List */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="p-4 border-b">
                    <h2 className="text-xl font-bold">Coupons List</h2>
                    
                    {/* Filter buttons */}
                    <div className="flex flex-wrap gap-2 mt-3">
                        <button 
                            onClick={() => fetchCoupons()}
                            className="px-3 py-1 text-sm bg-slate-100 rounded-full"
                        >
                            All
                        </button>
                        <button 
                            onClick={() => fetchCoupons('active')}
                            className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded-full"
                        >
                            Active
                        </button>
                        <button 
                            onClick={() => fetchCoupons('expired')}
                            className="px-3 py-1 text-sm bg-red-100 text-red-800 rounded-full"
                        >
                            Expired
                        </button>
                        <button 
                            onClick={() => fetchCoupons('upcoming')}
                            className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full"
                        >
                            Upcoming
                        </button>
                    </div>
                </div>
                
                {loading ? (
                    <div className="p-8 text-center">Loading coupons...</div>
                ) : coupons.length === 0 ? (
                    <div className="p-8 text-center text-slate-500">No coupons found</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full">
                            <thead className="bg-slate-50">
                                <tr>
                                    <th className="p-3 text-left">Code</th>
                                    <th className="p-3 text-left">Description</th>
                                    {/* ← নতুন কলাম যোগ করুন */}
                                    <th className="p-3 text-left">Store / Sector</th>
                                    <th className="p-3 text-left">Type</th>
                                    <th className="p-3 text-left">Discount</th>
                                    <th className="p-3 text-left">Status</th>
                                    <th className="p-3 text-left">Expires</th>
                                    <th className="p-3 text-left">Used</th>
                                    <th className="p-3 text-left">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {coupons.map((coupon) => (
                                    <tr key={coupon.id} className="hover:bg-slate-50">
                                        <td className="p-3 font-mono font-bold">{coupon.code}</td>
                                        <td className="p-3 max-w-xs truncate">{coupon.description}</td>

                                                                    {/* ← নতুন: Store / Sector কলাম */}
                                        <td className="p-3">
                                            {coupon.organization ? (
                                                <span className="inline-block px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
                                                    {organizationsMap[coupon.organization] || `Store #${coupon.organization}`}
                                                </span>
                                            ) : (
                                                <span className="inline-block px-2 py-1 bg-indigo-100 text-indigo-800 text-xs rounded-full">
                                                    Global / All Stores
                                                </span>
                                            )}
                                        </td>

                                        {/* ← নতুন: Type কলাম (কোন ধরনের কুপন) */}
                                        <td className="p-3">
                                            <div className="flex flex-wrap gap-1">
                                                {coupon.is_public && (
                                                    <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                                                        Public
                                                    </span>
                                                )}
                                                {coupon.for_new_user && (
                                                    <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                                                        New User
                                                    </span>
                                                )}
                                                {coupon.for_member && (
                                                    <span className="px-2 py-0.5 bg-amber-100 text-amber-800 text-xs rounded-full">
                                                        Member Only
                                                    </span>
                                                )}
                                                {!coupon.is_public && !coupon.for_new_user && !coupon.for_member && (
                                                    <span className="px-2 py-0.5 bg-gray-100 text-gray-800 text-xs rounded-full">
                                                        Private
                                                    </span>
                                                )}
                                            </div>
                                        </td>


                                        <td className="p-3 font-bold">{coupon.discount}%</td>
                                        <td className="p-3">{getStatusBadge(coupon)}</td>
                                        <td className="p-3">
                                            <div className="text-sm">
                                                {format(new Date(coupon.valid_to), 'MMM dd, yyyy')}
                                                <div className="text-xs text-slate-500 flex items-center gap-1">
                                                    <Clock size={12} />
                                                    {getTimeRemaining(coupon.valid_to)}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-3">
                                            {coupon.used_count} / {coupon.usage_limit}
                                        </td>
                                        <td className="p-3">
                                            <div className="flex items-center gap-2">

                                                {/* ← নতুন: Edit Button যোগ করা */}
                                    <button
                                        onClick={() => startEditCoupon(coupon)}
                                        className="p-1 rounded bg-blue-50 text-blue-600 hover:bg-blue-100"
                                        title="Edit Coupon"
                                    >
                                        <Edit size={18} />
                                    </button>
                                                <button
                                                    onClick={() => toggleCouponStatus(coupon)}
                                                    className={`p-1 rounded ${coupon.is_active ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}
                                                    title={coupon.is_active ? 'Deactivate' : 'Activate'}
                                                >
                                                    {coupon.is_active ? 
                                                        <ToggleRight size={20} /> : 
                                                        <ToggleLeft size={20} />
                                                    }
                                                </button>
                                                
                                                <button
                                                    onClick={() => deleteCoupon(coupon.code)}
                                                    className="p-1 rounded bg-red-50 text-red-600 hover:bg-red-100"
                                                    title="Delete"
                                                >
                                                    <DeleteIcon size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
            
            {/* System Info */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg text-sm">
                <div className="flex items-start gap-2">
                    <AlertCircle size={18} className="text-blue-600 mt-0.5" />
                    <div>
                        <h3 className="font-medium text-blue-800">System Information</h3>
                        <p className="text-blue-600">
                            Coupons are automatically expired at their exact expiry time using Celery tasks.
                            You can also manually activate/deactivate or delete coupons at any time.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}