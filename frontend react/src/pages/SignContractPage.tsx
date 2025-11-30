import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import SignatureCanvas from 'react-signature-canvas';
import { toast } from 'react-hot-toast';
import { CheckCircle } from 'lucide-react';
import { api } from '../utils/api';

interface Contract {
  id: string;
  title: string;
  client_name: string;
  content: string;
  status: 'draft' | 'sent' | 'signed';
  signed_at?: string;
}

export default function SignContractPage() {
  const { contractId } = useParams<{ contractId: string }>();
  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [signed, setSigned] = useState(false);
  const sigCanvas = useRef<SignatureCanvas>(null);

  const fetchContract = useCallback(async () => {
    try {
      // Use public endpoint
      const response = await api.get<Contract>(`/public/contracts/${contractId}`);
      if (response.success && response.data) {
        setContract(response.data);
        if (response.data.status === 'signed') {
          setSigned(true);
        }
      } else {
        setError(response.error || 'Failed to load contract');
      }
    } catch (err) {
      console.error('Error fetching contract:', err);
      setError('Failed to load contract');
    } finally {
      setLoading(false);
    }
  }, [contractId]);

  useEffect(() => {
    fetchContract();
  }, [fetchContract]);

  const handleClear = () => {
    sigCanvas.current?.clear();
  };

  const handleSubmit = async () => {
    if (sigCanvas.current?.isEmpty()) {
      toast.error('Please sign the contract');
      return;
    }

    const signatureData = sigCanvas.current?.getTrimmedCanvas().toDataURL('image/png');

    try {
      await api.post(`/public/contracts/${contractId}/sign`, {
        signature_data: signatureData
      });
      setSigned(true);
      toast.success('Contract signed successfully!');
    } catch (err) {
      console.error('Error signing contract:', err);
      toast.error('Failed to submit signature');
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading contract...</div>;
  if (error) return <div className="min-h-screen flex items-center justify-center text-red-600">{error}</div>;
  if (!contract) return null;

  return (
    <div className="min-h-screen bg-[#F5F5F7] py-12 px-4">
      <div className="max-w-3xl mx-auto bg-white rounded-3xl shadow-xl overflow-hidden">
        <div className="bg-[#1D1D1F] p-8 text-white">
          <h1 className="text-2xl font-bold mb-2">{contract.title}</h1>
          <div className="text-white/60 text-sm">
            Prepared for {contract.client_name}
          </div>
        </div>

        <div className="p-8">
          <div className="prose max-w-none mb-12 font-serif bg-gray-50 p-8 rounded-xl border border-gray-100 whitespace-pre-wrap">
            {contract.content}
          </div>

          {signed ? (
            <div className="bg-green-50 border border-green-100 rounded-2xl p-8 text-center">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-green-800 mb-2">Contract Signed</h2>
              <p className="text-green-600">
                This contract was legally signed on {new Date(contract.signed_at || new Date()).toLocaleDateString()}.
                <br />A copy has been sent to your email.
              </p>
            </div>
          ) : (
            <div className="border-t border-gray-100 pt-8">
              <h3 className="text-lg font-bold text-[#1D1D1F] mb-4">Sign Here</h3>
              <p className="text-sm text-gray-500 mb-4">
                By signing below, you agree to the terms and conditions outlined above.
              </p>
              
              <div className="border-2 border-dashed border-gray-300 rounded-xl overflow-hidden mb-4 relative bg-white">
                <SignatureCanvas 
                  ref={sigCanvas}
                  penColor="black"
                  canvasProps={{
                    className: 'w-full h-64 cursor-crosshair'
                  }} 
                />
                <div className="absolute bottom-2 left-4 text-xs text-gray-300 pointer-events-none">
                  X __________________________________________________
                </div>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handleClear}
                  className="px-6 py-3 bg-gray-100 text-gray-600 rounded-full font-medium hover:bg-gray-200 transition-colors"
                >
                  Clear Signature
                </button>
                <button
                  onClick={handleSubmit}
                  className="flex-1 px-6 py-3 bg-[#0066CC] text-white rounded-full font-bold hover:bg-[#0052A3] transition-colors shadow-lg shadow-blue-500/30"
                >
                  Confirm & Sign Contract
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      
      <div className="text-center mt-8 text-gray-400 text-sm">
        Powered by Galerly
      </div>
    </div>
  );
}

