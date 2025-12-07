import { useState, useEffect } from 'react';
import { Plus, Search, FileText, Send, Trash2, X, Printer, Lock } from 'lucide-react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { useBrandedModal } from '../components/BrandedModal';

interface InvoiceItem {
  description: string;
  quantity: number;
  price: number;
}

interface Invoice {
  id: string;
  client_name: string;
  client_email: string;
  status: 'draft' | 'sent' | 'paid' | 'cancelled';
  due_date: string;
  currency: string;
  items: InvoiceItem[];
  total_amount: number;
  notes: string;
  created_at: string;
}

export default function InvoicesPage() {
  const { user } = useAuth();
  const { showConfirm, ModalComponent } = useBrandedModal();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Plan gating
  const isAllowed = user?.plan === 'pro' || user?.plan === 'ultimate';

  // New Invoice Form State
  const [newInvoice, setNewInvoice] = useState<Partial<Invoice>>({
    client_name: '',
    client_email: '',
    due_date: '',
    currency: 'USD',
    items: [{ description: '', quantity: 1, price: 0 }],
    notes: ''
  });

  useEffect(() => {
    if (isAllowed) {
    fetchInvoices();
    } else {
      setLoading(false);
    }
  }, [isAllowed]);

  const fetchInvoices = async () => {
    try {
      const response = await api.get('/invoices');
      setInvoices(response.data.invoices);
    } catch (error) {
      console.error('Error fetching invoices:', error);
      toast.error('Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateInvoice = async () => {
    try {
      if (!newInvoice.client_email || !newInvoice.items?.length) {
        toast.error('Please fill in required fields');
        return;
      }
      
      await api.post('/invoices', newInvoice);
      toast.success('Invoice created successfully');
      setShowCreateModal(false);
      fetchInvoices();
      // Reset form
      setNewInvoice({
        client_name: '',
        client_email: '',
        due_date: '',
        currency: 'USD',
        items: [{ description: '', quantity: 1, price: 0 }],
        notes: ''
      });
    } catch (error) {
      console.error('Error creating invoice:', error);
      toast.error('Failed to create invoice');
    }
  };

  const handleDeleteInvoice = async (id: string) => {
    const confirmed = await showConfirm(
      'Delete Invoice',
      'Are you sure you want to delete this invoice?',
      'Delete',
      'Cancel',
      'danger'
    );
    
    if (!confirmed) return;
    
    try {
      await api.delete(`/invoices/${id}`);
      toast.success('Invoice deleted');
      setInvoices(invoices.filter(i => i.id !== id));
    } catch (error) {
      console.error('Error deleting invoice:', error);
      toast.error('Failed to delete invoice');
    }
  };

  const handleSendInvoice = async (id: string) => {
    try {
      await api.post(`/invoices/${id}/send`);
      toast.success('Invoice sent to client');
      fetchInvoices();
    } catch (error) {
      console.error('Error sending invoice:', error);
      toast.error('Failed to send invoice');
    }
  };

  const handlePrintInvoice = (invoice: Invoice) => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const html = `
      <html>
        <head>
          <title>Invoice #${invoice.id}</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 40px; color: #1D1D1F; }
            .header { display: flex; justify-content: space-between; margin-bottom: 60px; }
            .brand { font-size: 24px; font-weight: bold; margin-bottom: 20px; }
            .title { font-size: 42px; font-weight: bold; margin-bottom: 10px; }
            .meta { text-align: right; line-height: 1.6; }
            .bill-to { line-height: 1.6; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 40px; }
            th { text-align: left; border-bottom: 2px solid #E5E5E5; padding: 16px 8px; font-size: 12px; text-transform: uppercase; color: #86868B; }
            td { border-bottom: 1px solid #E5E5E5; padding: 16px 8px; font-size: 14px; }
            .total-section { display: flex; justify-content: flex-end; }
            .total-row { display: flex; justify-content: space-between; width: 300px; padding: 10px 0; }
            .total-final { font-size: 24px; font-weight: bold; border-top: 2px solid #E5E5E5; padding-top: 20px; margin-top: 10px; }
            .notes { margin-top: 60px; padding: 20px; background: #F5F5F7; border-radius: 12px; font-size: 14px; color: #424245; }
            @media print {
                body { padding: 0; }
                .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <div class="brand">Galerly</div>
              <div class="bill-to">
                <strong>Bill To:</strong><br>
                ${invoice.client_name}<br>
                ${invoice.client_email}
              </div>
            </div>
            <div class="meta">
              <div class="title">INVOICE</div>
              <p>
                <strong>Invoice #:</strong> ${invoice.id.slice(0, 8).toUpperCase()}<br>
                <strong>Date:</strong> ${new Date(invoice.created_at).toLocaleDateString()}<br>
                <strong>Due Date:</strong> ${invoice.due_date || 'Due on receipt'}
              </p>
            </div>
          </div>
          
          <table>
            <thead>
              <tr>
                <th>Description</th>
                <th style="width: 80px;">Qty</th>
                <th style="width: 120px;">Price</th>
                <th style="text-align: right; width: 120px;">Total</th>
              </tr>
            </thead>
            <tbody>
              ${invoice.items.map(item => `
                <tr>
                  <td>${item.description}</td>
                  <td>${item.quantity}</td>
                  <td>${Number(item.price).toLocaleString('en-US', { style: 'currency', currency: invoice.currency })}</td>
                  <td style="text-align: right;">${(item.quantity * item.price).toLocaleString('en-US', { style: 'currency', currency: invoice.currency })}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          
          <div class="total-section">
            <div>
                <div class="total-row total-final">
                    <span>Total</span>
                    <span>${Number(invoice.total_amount).toLocaleString('en-US', { style: 'currency', currency: invoice.currency })}</span>
                </div>
            </div>
          </div>
          
          ${invoice.notes ? `<div class="notes"><strong>Notes:</strong><br>${invoice.notes}</div>` : ''}
          
          <script>
            window.onload = () => { setTimeout(() => window.print(), 500); }
          </script>
        </body>
      </html>
    `;
    
    printWindow.document.write(html);
    printWindow.document.close();
  };

  const addItem = () => {
    setNewInvoice({
      ...newInvoice,
      items: [...(newInvoice.items || []), { description: '', quantity: 1, price: 0 }]
    });
  };

  const removeItem = (index: number) => {
    const items = [...(newInvoice.items || [])];
    items.splice(index, 1);
    setNewInvoice({ ...newInvoice, items });
  };

  const updateItem = (index: number, field: keyof InvoiceItem, value: string | number) => {
    const items = [...(newInvoice.items || [])];
    items[index] = { ...items[index], [field]: value };
    setNewInvoice({ ...newInvoice, items });
  };

  const calculateTotal = () => {
    return (newInvoice.items || []).reduce((sum, item) => sum + (item.quantity * item.price), 0);
  };

  const filteredInvoices = invoices.filter(inv => 
    inv.client_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    inv.client_email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isAllowed) {
    return (
      <div className="min-h-screen bg-[#F5F5F7]">
        <Header />
        <main className="pt-32 pb-20 px-4 md:px-6 max-w-7xl mx-auto text-center">
          <div className="max-w-md mx-auto">
            <div className="w-16 h-16 bg-gray-900 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl">
              <Lock className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-[#1D1D1F] mb-4">Client Invoicing</h1>
            <p className="text-[#1D1D1F]/70 text-lg mb-8">
              Create and send professional invoices directly to your clients. Track payments and manage your business finances in one place.
            </p>
            <div className="bg-white p-6 rounded-2xl border border-gray-200 mb-8 text-left">
              <h3 className="font-semibold text-[#1D1D1F] mb-4">Pro Plan Features:</h3>
              <ul className="space-y-3">
                <li className="flex items-center gap-3 text-sm text-[#1D1D1F]/80">
                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  Unlimited Invoices
                </li>
                <li className="flex items-center gap-3 text-sm text-[#1D1D1F]/80">
                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  Multi-currency Support
                </li>
                <li className="flex items-center gap-3 text-sm text-[#1D1D1F]/80">
                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                  PDF Generation & Email Sending
                </li>
              </ul>
            </div>
            <Link 
              to="/billing" 
              className="inline-flex items-center justify-center px-8 py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Upgrade to Pro
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      <Header />
      
      <main className="pt-24 pb-20 px-4 md:px-6 max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-[#1D1D1F]">Invoices</h1>
            <p className="text-[#1D1D1F]/60 mt-1">Manage billing and payments</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-6 py-2.5 bg-[#1D1D1F] text-white rounded-full hover:bg-black transition-colors"
          >
            <Plus className="w-4 h-4" /> Create Invoice
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-2xl p-4 mb-6 shadow-sm border border-gray-100 flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search clients..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
            />
          </div>
        </div>

        {/* List */}
        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-400">Loading invoices...</div>
          ) : filteredInvoices.length === 0 ? (
            <div className="p-12 text-center text-gray-400">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>No invoices found</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="text-left py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Client</th>
                  <th className="text-left py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="text-left py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="text-right py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="text-right py-4 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredInvoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="py-4 px-6">
                      <div className="font-medium text-[#1D1D1F]">{invoice.client_name || 'Unnamed Client'}</div>
                      <div className="text-xs text-gray-500">{invoice.client_email}</div>
                    </td>
                    <td className="py-4 px-6 text-sm text-gray-600">
                      {new Date(invoice.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
                        ${invoice.status === 'paid' ? 'bg-green-100 text-green-800' : 
                          invoice.status === 'sent' ? 'bg-blue-100 text-blue-800' : 
                          'bg-gray-100 text-gray-800'}`}>
                        {invoice.status}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right font-medium text-[#1D1D1F]">
                      {Number(invoice.total_amount).toLocaleString('en-US', { style: 'currency', currency: invoice.currency })}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => handlePrintInvoice(invoice)}
                          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                          title="Print / PDF"
                        >
                          <Printer className="w-4 h-4" />
                        </button>
                        {invoice.status === 'draft' && (
                          <button 
                            onClick={() => handleSendInvoice(invoice.id)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Send Invoice"
                          >
                            <Send className="w-4 h-4" />
                          </button>
                        )}
                        <button 
                          onClick={() => handleDeleteInvoice(invoice.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-3xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="p-6 border-b border-gray-100 flex justify-between items-center sticky top-0 bg-white z-10">
              <h2 className="text-xl font-bold text-[#1D1D1F]">New Invoice</h2>
              <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-gray-100 rounded-full">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Client Name</label>
                  <input
                    type="text"
                    value={newInvoice.client_name}
                    onChange={e => setNewInvoice({...newInvoice, client_name: e.target.value})}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Client Email *</label>
                  <input
                    type="email"
                    value={newInvoice.client_email}
                    onChange={e => setNewInvoice({...newInvoice, client_email: e.target.value})}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                  <input
                    type="date"
                    value={newInvoice.due_date}
                    onChange={e => setNewInvoice({...newInvoice, due_date: e.target.value})}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                  <select
                    value={newInvoice.currency}
                    onChange={e => setNewInvoice({...newInvoice, currency: e.target.value})}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                  >
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                  </select>
                </div>
              </div>

              {/* Items */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Line Items</label>
                <div className="space-y-3">
                  {newInvoice.items?.map((item, index) => (
                    <div key={index} className="flex gap-2 items-start">
                      <input
                        type="text"
                        placeholder="Description"
                        value={item.description}
                        onChange={e => updateItem(index, 'description', e.target.value)}
                        className="flex-1 px-4 py-2 rounded-xl border border-gray-200"
                      />
                      <input
                        type="number"
                        placeholder="Qty"
                        value={item.quantity}
                        onChange={e => updateItem(index, 'quantity', Number(e.target.value))}
                        className="w-20 px-4 py-2 rounded-xl border border-gray-200"
                      />
                      <input
                        type="number"
                        placeholder="Price"
                        value={item.price}
                        onChange={e => updateItem(index, 'price', Number(e.target.value))}
                        className="w-32 px-4 py-2 rounded-xl border border-gray-200"
                      />
                      <button 
                        onClick={() => removeItem(index)}
                        className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={addItem}
                    className="text-sm text-[#0066CC] hover:underline font-medium flex items-center gap-1"
                  >
                    <Plus className="w-3 h-3" /> Add Item
                  </button>
                </div>
              </div>

              <div className="flex justify-end border-t border-gray-100 pt-4">
                 <div className="text-right">
                   <span className="text-gray-500 text-sm">Total Amount</span>
                   <div className="text-2xl font-bold text-[#1D1D1F]">
                     {calculateTotal().toLocaleString('en-US', { style: 'currency', currency: newInvoice.currency })}
                   </div>
                 </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={newInvoice.notes}
                  onChange={e => setNewInvoice({...newInvoice, notes: e.target.value})}
                  className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                  rows={3}
                  placeholder="Payment instructions, thank you note, etc."
                />
              </div>
            </div>

            <div className="p-6 border-t border-gray-100 bg-gray-50 rounded-b-3xl flex justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-6 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-full font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateInvoice}
                className="px-6 py-2.5 bg-[#1D1D1F] text-white rounded-full font-medium hover:bg-black"
              >
                Create Invoice
              </button>
            </div>
          </div>
        </div>
      )}
      <Footer />

      {/* Branded Modal */}
      <ModalComponent />
    </div>
  );
}

