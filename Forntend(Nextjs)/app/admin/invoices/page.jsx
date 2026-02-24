// app/admin/invoices/page.jsx
'use client'

import { useState, useEffect } from 'react'
import axios from '@/api/AxiosInstance'

const InvoicesPage = () => {
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchInvoices = async () => {
    try {
      const res = await axios.get('/admin/invoices/')
      setInvoices(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInvoices()
  }, [])

  const handleStatusChange = async (id, status) => {
    if (!confirm(`Change invoice status to ${status}?`)) return
    try {
      const res = await axios.patch(`/admin/invoices/${id}/`, { status })
      setInvoices(invoices.map(inv => inv.id === id ? res.data : inv))
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Invoices</h1>

      {loading ? (
        <p>Loading...</p>
      ) : invoices.length === 0 ? (
        <p>No invoices found.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full table-auto border border-slate-200 rounded">
            <thead className="bg-slate-100">
              <tr>
                <th className="p-2 border">Invoice #</th>
                <th className="p-2 border">Organization</th>
                <th className="p-2 border">Amount</th>
                <th className="p-2 border">Status</th>
                <th className="p-2 border">Issued At</th>
                <th className="p-2 border">Due At</th>
                <th className="p-2 border">PDF</th>
                <th className="p-2 border">Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map(inv => (
                <tr key={inv.id} className="hover:bg-slate-50">
                  <td className="p-2 border">{inv.invoice_number}</td>
                  <td className="p-2 border">{inv.organization.business_name}</td>
                  <td className="p-2 border">{inv.amount} {inv.currency}</td>
                  <td className="p-2 border capitalize">{inv.status}</td>
                  <td className="p-2 border">{new Date(inv.issued_at).toLocaleDateString()}</td>
                  <td className="p-2 border">{new Date(inv.due_at).toLocaleDateString()}</td>
                  <td className="p-2 border">
                    {inv.pdf_url ? (
                      <a href={inv.pdf_url} target="_blank" className="text-blue-500 hover:underline">View PDF</a>
                    ) : '-'}
                  </td>
                  <td className="p-2 border flex gap-2">
                    {inv.status !== 'paid' && (
                      <button onClick={() => handleStatusChange(inv.id, 'paid')} className="text-green-500 hover:text-green-700">Mark Paid</button>
                    )}
                    {inv.status !== 'pending' && (
                      <button onClick={() => handleStatusChange(inv.id, 'pending')} className="text-yellow-500 hover:text-yellow-700">Mark Pending</button>
                    )}
                    {inv.status !== 'failed' && (
                      <button onClick={() => handleStatusChange(inv.id, 'failed')} className="text-red-500 hover:text-red-700">Mark Failed</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default InvoicesPage