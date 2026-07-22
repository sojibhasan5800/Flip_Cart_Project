// app/admin/subscription-plans/create/page.jsx
'use client'

import { useState } from 'react'
import axios from '@/api/AxiosInstance'
import { useRouter } from 'next/navigation'

const SubscriptionPlanForm = () => {
  const router = useRouter()
  const [form, setForm] = useState({

  // -----------------------
  // Basic Plan
  // -----------------------
  name: "",
  slug: "",
  plan_level: "basic",
  plan_type: "general",

  price: 0,
  currency: "USD",

  billing_cycle: "monthly",
  duration_days: 30,

  max_users: 1,
  max_products: 100,
  max_boosted_products: 0,
  storage_gb: 5,

  features: {},
  is_active: true,

  // -----------------------
  // Shipping
  // -----------------------

  free_shipping: false,
  free_shipping_min_order: 0,
  max_free_shipping_orders: 999999,
  shipping_discount_percent: 0,

  // -----------------------
  // Membership Benefits
  // -----------------------

  priority_order_processing: false,
  priority_customer_support: false,
  early_access_sale: false,
  exclusive_deals: false,

  cashback_percent: 0,
  reward_points_multiplier: 1,

  // -----------------------
  // Profit Protection
  // -----------------------

  monthly_order_limit: 0,
  monthly_spending_limit: 0,

  // -----------------------
  // Display
  // -----------------------

  display_order: 0,
  recommended: false,
  badge: "",
});

const generateSlug = (text) => {
  return text
    .toLowerCase()
    .trim()
    .replace(/[\s\W-]+/g, '-')
}



const handleChange = (e) => {
  const { name, value, type, checked } = e.target;

  setForm((prev) => {

    let updated = {
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    };

    // Name change হলে slug auto generate
    if (name === "name") {
      updated.slug = generateSlug(value);
    }

    return updated;
  });
};

  const handleSubmit = async e => {
    e.preventDefault()
    try {
      await axios.post('api/billing/plans/', form)
      router.push('/admin/subscription-plans')
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Create Subscription Plan</h1>
      <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
        <div>
          <label className="block mb-1">Name</label>
          <input type="text" name="name" value={form.name} onChange={handleChange} className="w-full border p-2 rounded" />
        </div>
        <div>
          <label className="block mb-1">Slug</label>
          <input type="text" name="slug" value={form.slug} onChange={handleChange} className="w-full border p-2 rounded" />
        </div>
        <div className="flex gap-2">
          <div className="flex-1">
            <label>Level</label>
            <select name="plan_level" value={form.plan_level} onChange={handleChange} className="w-full border p-2 rounded">
              <option value="basic">Basic</option>
              <option value="premium">Premium</option>
              <option value="standard">Standard</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          <div className="flex-1">
            <label>Type</label>
            <select name="plan_type" value={form.plan_type} onChange={handleChange} className="w-full border p-2 rounded">
              <option value="general">General</option>
              <option value="product_boost">Product Boost</option>
              <option value="plus_membership">Plus Membership</option>
              <option value="organization">Organization</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2">
          <div className="flex-1">
            <label>Price</label>
            <input type="number" name="price" value={form.price} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
          <div className="flex-1">
            <label>Currency</label>
            <input type="text" name="currency" value={form.currency} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
        </div>

        <div className="flex gap-2">
          <div className="flex-1">
            <label>Billing Cycle</label>
            <select name="billing_cycle" value={form.billing_cycle} onChange={handleChange} className="w-full border p-2 rounded">
               <option value="7_days">7 Days</option>
                <option value="15_days">15 Days</option>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly (3 Months)</option>
                <option value="half_yearly">Half Yearly (6 Months)</option>
                <option value="yearly">Yearly</option>
            </select>
          </div>
          <div className="flex-1">
            <label>Duration Days</label>
            <input type="number" name="duration_days" value={form.duration_days} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
        </div>

        {/* ===========================
    PLUS MEMBERSHIP ONLY
=========================== */}

{form.plan_type === "plus_membership" && (
  <div className="border rounded-lg p-5 mt-6">

    <h2 className="font-bold text-xl mb-4">
      Shipping Benefits
    </h2>

    <div className="grid grid-cols-2 gap-4">

      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          name="free_shipping"
          checked={form.free_shipping}
          onChange={handleChange}
        />
        Free Shipping
      </label>

      <div>
        <label>Minimum Order</label>
        <input
          type="number"
          name="free_shipping_min_order"
          value={form.free_shipping_min_order}
          onChange={handleChange}
          className="w-full border rounded p-2"
        />
      </div>

      <div>
        <label>Max Free Orders</label>
        <input
          type="number"
          name="max_free_shipping_orders"
          value={form.max_free_shipping_orders}
          onChange={handleChange}
          className="w-full border rounded p-2"
        />
      </div>

      <div>
        <label>Shipping Discount %</label>
        <input
          type="number"
          name="shipping_discount_percent"
          value={form.shipping_discount_percent}
          onChange={handleChange}
          className="w-full border rounded p-2"
        />
      </div>

    </div>

  </div>
)}

{form.plan_type==="plus_membership" && (

<div className="border rounded-lg p-5 mt-5">

<h2 className="font-bold text-xl mb-4">

Membership Benefits

</h2>

<div className="grid grid-cols-2 gap-4">

<label>

<input
type="checkbox"
name="priority_order_processing"
checked={form.priority_order_processing}
onChange={handleChange}
/>

Priority Orders

</label>

<label>

<input
type="checkbox"
name="priority_customer_support"
checked={form.priority_customer_support}
onChange={handleChange}
/>

Priority Support

</label>

<label>

<input
type="checkbox"
name="early_access_sale"
checked={form.early_access_sale}
onChange={handleChange}
/>

Early Access Sale

</label>

<label>

<input
type="checkbox"
name="exclusive_deals"
checked={form.exclusive_deals}
onChange={handleChange}
/>

Exclusive Deals

</label>

<div>

<label>Cashback %</label>

<input
type="number"
name="cashback_percent"
value={form.cashback_percent}
onChange={handleChange}
className="w-full border rounded p-2"
/>

</div>

<div>

<label>Reward Multiplier</label>

<input
type="number"
step="0.1"
name="reward_points_multiplier"
value={form.reward_points_multiplier}
onChange={handleChange}
className="w-full border rounded p-2"
/>

</div>

</div>

</div>

)}
{/* Plus Membership Settings */}
{form.plan_type === "plus_membership" && (

<div className="border rounded-lg p-5 mt-5">

<h2 className="font-bold text-xl mb-4">
Profit Protection
</h2>

<div className="grid grid-cols-2 gap-4">

<div>
<label>Monthly Order Limit</label>

<input
type="number"
name="monthly_order_limit"
value={form.monthly_order_limit}
onChange={handleChange}
className="w-full border rounded p-2"
/>

</div>

<div>

<label>Monthly Spending Limit</label>

<input
type="number"
name="monthly_spending_limit"
value={form.monthly_spending_limit}
onChange={handleChange}
className="w-full border rounded p-2"
/>

</div>

</div>

</div>

)}
{form.plan_type==="plus_membership" && (

<div className="border rounded-lg p-5 mt-5">

<h2 className="font-bold text-xl">

Display Settings

</h2>

<div className="grid grid-cols-2 gap-4 mt-4">

<div>

<label>Display Order</label>

<input
type="number"
name="display_order"
value={form.display_order}
onChange={handleChange}
className="w-full border rounded p-2"
/>

</div>

<div>

<label>Badge</label>

<input
type="text"
name="badge"
value={form.badge}
onChange={handleChange}
className="w-full border rounded p-2"
placeholder="Most Popular"
/>

</div>

<label>

<input
type="checkbox"
name="recommended"
checked={form.recommended}
onChange={handleChange}
/>

Recommended Plan

</label>

</div>

</div>

)}



        <button type="submit" className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">Create Plan</button>
      </form>
    </div>
  )
}

export default SubscriptionPlanForm