'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Lock,
  CreditCard,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ShieldCheck,
  Sparkles,
  QrCode,
  Building,
  Zap,
  Check
} from 'lucide-react';

interface CreatorUpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (updatedSubscription?: any) => void;
}

// Client-side Validation Helpers
export function validateLuhn(cardNumber: string): boolean {
  const cleanNum = cardNumber.replace(/\s+/g, '');
  if (!/^\d{13,19}$/.test(cleanNum)) return false;
  
  let sum = 0;
  let shouldDouble = false;
  for (let i = cleanNum.length - 1; i >= 0; i--) {
    let digit = parseInt(cleanNum.charAt(i), 10);
    if (shouldDouble) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
    shouldDouble = !shouldDouble;
  }
  return sum % 10 === 0;
}

export function validateExpiry(expiry: string): boolean {
  const clean = expiry.replace(/\s+|\//g, '');
  if (!/^\d{4}$/.test(clean)) return false;
  
  const month = parseInt(clean.substring(0, 2), 10);
  const year = parseInt('20' + clean.substring(2, 4), 10);
  if (month < 1 || month > 12) return false;

  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

  if (year < currentYear) return false;
  if (year === currentYear && month < currentMonth) return false;
  if (year > currentYear + 25) return false;
  
  return true;
}

export function validateCVV(cvv: string): boolean {
  return /^\d{3,4}$/.test(cvv.trim());
}

export function validateName(name: string): boolean {
  return name.trim().length >= 2;
}

export default function CreatorUpgradeModal({
  isOpen,
  onClose,
  onSuccess
}: CreatorUpgradeModalProps) {
  const router = useRouter();
  
  // Checkout Method Selection: 'card' | 'upi' | 'netbanking'
  const [paymentMethod, setPaymentMethod] = useState<'card' | 'upi' | 'netbanking'>('card');

  // Input State
  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvv, setCvv] = useState('');
  const [nameOnCard, setNameOnCard] = useState('Prachi Zala');
  const [upiId, setUpiId] = useState('user@upi');
  const [selectedBank, setSelectedBank] = useState('HDFC Bank');

  // Order & Session State
  const [orderId, setOrderId] = useState<string | null>(null);
  const [isInitializingOrder, setIsInitializingOrder] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  // Confetti Canvas Ref
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Initialize Checkout Order on Modal Open
  useEffect(() => {
    if (isOpen) {
      setIsSuccess(false);
      setErrorMessage(null);
      fetchCheckoutOrder();
    }
  }, [isOpen]);

  const fetchCheckoutOrder = async () => {
    setIsInitializingOrder(true);
    try {
      const res = await fetch('/api/subscription/create-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan: 'creator',
          amount: 499,
          currency: 'INR'
        })
      });
      if (res.ok) {
        const data = await res.json();
        setOrderId(data.order_id);
      }
    } catch (err) {
      console.error('Failed to create subscription order:', err);
    } finally {
      setIsInitializingOrder(false);
    }
  };

  // Input Handlers
  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 16);
    const formatted = raw.match(/.{1,4}/g)?.join(' ') || raw;
    setCardNumber(formatted);
    if (errorMessage) setErrorMessage(null);
  };

  const handleExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let raw = e.target.value.replace(/\D/g, '').slice(0, 4);
    let formatted = raw;
    if (raw.length >= 3) {
      formatted = `${raw.slice(0, 2)} / ${raw.slice(2)}`;
    }
    setExpiry(formatted);
    if (errorMessage) setErrorMessage(null);
  };

  const handleCvvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 4);
    setCvv(raw);
    if (errorMessage) setErrorMessage(null);
  };

  // Validations
  const isCardValid = validateLuhn(cardNumber);
  const isExpiryValid = validateExpiry(expiry);
  const isCvvValid = validateCVV(cvv);
  const isNameValid = validateName(nameOnCard);

  const isFormValid =
    paymentMethod === 'card'
      ? isCardValid && isExpiryValid && isCvvValid && isNameValid
      : paymentMethod === 'upi'
      ? upiId.includes('@')
      : true;

  // Trigger Canvas Confetti
  const runConfetti = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.offsetWidth || 480;
    canvas.height = canvas.offsetHeight || 480;

    const particles: Array<{
      x: number;
      y: number;
      vx: number;
      vy: number;
      color: string;
      size: number;
      rotation: number;
      rSpeed: number;
    }> = [];

    const colors = ['#10B981', '#3B82F6', '#F59E0B', '#EC4899', '#8B5CF6', '#14B8A6'];
    for (let i = 0; i < 90; i++) {
      particles.push({
        x: canvas.width / 2,
        y: canvas.height / 3,
        vx: (Math.random() - 0.5) * 14,
        vy: (Math.random() - 0.8) * 12,
        color: colors[Math.floor(Math.random() * colors.length)],
        size: Math.random() * 8 + 4,
        rotation: Math.random() * 360,
        rSpeed: (Math.random() - 0.5) * 12
      });
    }

    let animId: number;
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      let alive = false;
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.28;
        p.rotation += p.rSpeed;
        if (p.y < canvas.height) alive = true;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
        ctx.restore();
      });

      if (alive) {
        animId = requestAnimationFrame(render);
      }
    };
    render();
  };

  useEffect(() => {
    if (isSuccess) {
      setTimeout(() => {
        runConfetti();
      }, 50);
    }
  }, [isSuccess]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (paymentMethod === 'card') {
      if (!isCardValid) {
        setErrorMessage('Please enter a valid 16-digit card number.');
        return;
      }
      if (!isExpiryValid) {
        setErrorMessage('Please enter a valid future expiration date (MM / YY).');
        return;
      }
      if (!isCvvValid) {
        setErrorMessage('Please enter a valid 3 or 4 digit CVV code.');
        return;
      }
      if (!isNameValid) {
        setErrorMessage('Please enter the full name on the card.');
        return;
      }
    }

    setIsProcessing(true);

    try {
      const paymentId = `pay_qoneqt_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
      const response = await fetch('/api/subscription/capture-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan: 'creator',
          amount: 499,
          order_id: orderId || `order_qoneqt_${Date.now()}`,
          payment_id: paymentId,
          card_number: cardNumber,
          expiry: expiry,
          cvv: cvv,
          name_on_card: nameOnCard
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Payment capture failed. Please try again.');
      }

      setIsSuccess(true);

      // Persist local state for instant UI updates
      if (typeof window !== 'undefined') {
        localStorage.setItem('user_subscription_tier', 'CREATOR');
        localStorage.setItem('user_subscription_status', 'ACTIVE');
        localStorage.setItem('user_videos_remaining', '15');
        localStorage.setItem('user_videos_limit', '15');
        localStorage.setItem('creator_plan_activated_banner', 'true');
      }

      if (onSuccess) {
        onSuccess(data.subscription);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'An unexpected error occurred during payment processing.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReturnToDashboard = () => {
    onClose();
    router.push('/dashboard?activated=true');
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#121316] border border-[#27272a] rounded-2xl max-w-md w-full p-6 md:p-7 shadow-2xl relative overflow-hidden text-zinc-100 font-sans">
        
        {/* Confetti Canvas */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 pointer-events-none z-20 w-full h-full"
        />

        {isSuccess ? (
          /* Payment Success View */
          <div className="text-center py-6 space-y-5 z-10 relative">
            <div className="inline-flex p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full mb-1">
              <CheckCircle2 className="w-12 h-12 animate-bounce" />
            </div>
            
            <div className="space-y-2">
              <span className="text-xs font-bold text-emerald-400 tracking-wider uppercase font-mono">
                Order Completed • {orderId || 'SUCCESS'}
              </span>
              <h2 className="text-2xl font-extrabold text-white">
                Payment Successful!
              </h2>
              <p className="text-sm text-zinc-400 max-w-xs mx-auto">
                Welcome to the <strong className="text-white font-semibold">CREATOR PLAN</strong>. You now have <strong className="text-emerald-400 font-bold">15 videos/month</strong> unlocked!
              </p>
            </div>

            <div className="p-4 bg-zinc-900/90 border border-zinc-800 rounded-xl text-xs space-y-2 text-left">
              <div className="flex justify-between">
                <span className="text-zinc-400">Plan:</span>
                <span className="font-semibold text-white">Creator (Monthly Recurring)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Amount Paid:</span>
                <span className="font-semibold text-emerald-400">₹499 INR</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Monthly Video Quota:</span>
                <span className="font-bold text-white">15 Videos / Month</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Scriptwriting Quota:</span>
                <span className="font-bold text-white">100 Scripts / Month</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Status:</span>
                <span className="font-semibold text-emerald-400">ACTIVE</span>
              </div>
            </div>

            <button
              onClick={handleReturnToDashboard}
              className="w-full py-3.5 px-4 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold rounded-xl text-sm transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4 fill-current" />
              <span>Go to Dashboard (Creator Plan Active)</span>
            </button>
          </div>
        ) : (
          /* Checkout Modal View */
          <div className="space-y-5">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#27272a] pb-4">
              <button
                type="button"
                onClick={onClose}
                disabled={isProcessing}
                className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-zinc-800/60 transition-colors disabled:opacity-50"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <h2 className="text-lg font-bold text-white">
                Complete your upgrade
              </h2>
              <div className="w-12"></div>
            </div>

            {/* Plan Overview & Price Banner */}
            <div className="p-4 bg-zinc-950 border border-zinc-800/80 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-emerald-400 tracking-wider uppercase font-mono">
                  CREATOR PLAN
                </span>
                <span className="text-[10px] bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-bold">
                  15 Videos/mo
                </span>
              </div>

              <div className="flex items-baseline justify-between pt-1">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-3xl font-extrabold text-white tracking-tight">
                    ₹499
                  </span>
                  <span className="text-xs text-zinc-400 font-medium">
                    / month
                  </span>
                </div>
                {orderId && (
                  <span className="text-[10px] text-zinc-500 font-mono">
                    ID: {orderId.slice(0, 18)}...
                  </span>
                )}
              </div>
            </div>

            {/* Payment Method Selector */}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setPaymentMethod('card')}
                className={`p-2.5 rounded-xl border font-medium flex flex-col items-center gap-1 transition-colors ${
                  paymentMethod === 'card'
                    ? 'bg-zinc-800 border-emerald-500 text-white'
                    : 'bg-zinc-950 border-[#27272a] text-zinc-400 hover:border-zinc-700'
                }`}
              >
                <CreditCard className="w-4 h-4 text-emerald-400" />
                <span>Card</span>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod('upi')}
                className={`p-2.5 rounded-xl border font-medium flex flex-col items-center gap-1 transition-colors ${
                  paymentMethod === 'upi'
                    ? 'bg-zinc-800 border-emerald-500 text-white'
                    : 'bg-zinc-950 border-[#27272a] text-zinc-400 hover:border-zinc-700'
                }`}
              >
                <QrCode className="w-4 h-4 text-emerald-400" />
                <span>UPI / QR</span>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod('netbanking')}
                className={`p-2.5 rounded-xl border font-medium flex flex-col items-center gap-1 transition-colors ${
                  paymentMethod === 'netbanking'
                    ? 'bg-zinc-800 border-emerald-500 text-white'
                    : 'bg-zinc-950 border-[#27272a] text-zinc-400 hover:border-zinc-700'
                }`}
              >
                <Building className="w-4 h-4 text-emerald-400" />
                <span>Netbanking</span>
              </button>
            </div>

            {/* Error Banner */}
            {errorMessage && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-start gap-2.5 animate-fadeIn">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div className="flex-1">{errorMessage}</div>
              </div>
            )}

            {/* Checkout Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {paymentMethod === 'card' && (
                <>
                  {/* Card Number */}
                  <div className="space-y-1.5">
                    <label className="block text-xs font-medium text-zinc-300">
                      Card Number
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        value={cardNumber}
                        onChange={handleCardNumberChange}
                        placeholder="1234 5678 9012 3456"
                        disabled={isProcessing}
                        className={`w-full bg-zinc-950 border ${
                          cardNumber && !isCardValid ? 'border-rose-500' : 'border-[#27272a] focus:border-zinc-500'
                        } rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-zinc-600 focus:outline-none transition-colors pr-10 font-mono`}
                      />
                      <CreditCard className="w-4 h-4 text-zinc-500 absolute right-3.5 top-3 pointer-events-none" />
                    </div>
                  </div>

                  {/* Expiry & CVV Grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <label className="block text-xs font-medium text-zinc-300">
                        Expiry Date
                      </label>
                      <input
                        type="text"
                        value={expiry}
                        onChange={handleExpiryChange}
                        placeholder="MM / YY"
                        disabled={isProcessing}
                        className={`w-full bg-zinc-950 border ${
                          expiry && !isExpiryValid ? 'border-rose-500' : 'border-[#27272a] focus:border-zinc-500'
                        } rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-zinc-600 focus:outline-none transition-colors font-mono text-center`}
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="block text-xs font-medium text-zinc-300">
                        CVV / CVC
                      </label>
                      <input
                        type="password"
                        value={cvv}
                        onChange={handleCvvChange}
                        placeholder="•••"
                        maxLength={4}
                        disabled={isProcessing}
                        className={`w-full bg-zinc-950 border ${
                          cvv && !isCvvValid ? 'border-rose-500' : 'border-[#27272a] focus:border-zinc-500'
                        } rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-zinc-600 focus:outline-none transition-colors font-mono text-center`}
                      />
                    </div>
                  </div>

                  {/* Name on Card */}
                  <div className="space-y-1.5">
                    <label className="block text-xs font-medium text-zinc-300">
                      Name on Card
                    </label>
                    <input
                      type="text"
                      value={nameOnCard}
                      onChange={(e) => {
                        setNameOnCard(e.target.value);
                        if (errorMessage) setErrorMessage(null);
                      }}
                      placeholder="Prachi Zala"
                      disabled={isProcessing}
                      className="w-full bg-zinc-950 border border-[#27272a] focus:border-zinc-500 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-zinc-600 focus:outline-none transition-colors"
                    />
                  </div>
                </>
              )}

              {paymentMethod === 'upi' && (
                <div className="space-y-3 py-1">
                  <div className="space-y-1.5">
                    <label className="block text-xs font-medium text-zinc-300">
                      VPA / UPI ID
                    </label>
                    <input
                      type="text"
                      value={upiId}
                      onChange={(e) => setUpiId(e.target.value)}
                      placeholder="username@upi"
                      disabled={isProcessing}
                      className="w-full bg-zinc-950 border border-[#27272a] focus:border-zinc-500 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-zinc-600 focus:outline-none font-mono"
                    />
                  </div>
                  <p className="text-[11px] text-zinc-400">
                    Supports Google Pay, PhonePe, Paytm, BHIM & all UPI apps.
                  </p>
                </div>
              )}

              {paymentMethod === 'netbanking' && (
                <div className="space-y-3 py-1">
                  <div className="space-y-1.5">
                    <label className="block text-xs font-medium text-zinc-300">
                      Select Bank
                    </label>
                    <select
                      value={selectedBank}
                      onChange={(e) => setSelectedBank(e.target.value)}
                      disabled={isProcessing}
                      className="w-full bg-zinc-950 border border-[#27272a] focus:border-zinc-500 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none"
                    >
                      <option value="HDFC Bank">HDFC Bank</option>
                      <option value="ICICI Bank">ICICI Bank</option>
                      <option value="State Bank of India">State Bank of India (SBI)</option>
                      <option value="Axis Bank">Axis Bank</option>
                      <option value="Kotak Mahindra Bank">Kotak Mahindra Bank</option>
                    </select>
                  </div>
                  <p className="text-[11px] text-zinc-400">
                    You will be redirected to your bank's secure authorization portal.
                  </p>
                </div>
              )}

              {/* Security Badge */}
              <div className="flex items-center justify-center gap-1.5 text-xs text-zinc-500 pt-1">
                <Lock className="w-3.5 h-3.5 text-zinc-400" />
                <span>Secure 256-bit encrypted payment via Razorpay / Stripe</span>
              </div>

              {/* Action Button */}
              <button
                type="submit"
                disabled={!isFormValid || isProcessing || isInitializingOrder}
                className="w-full py-3.5 px-4 bg-white hover:bg-zinc-200 text-zinc-950 font-bold rounded-xl text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg flex items-center justify-center gap-2 mt-2"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-zinc-950" />
                    <span>Processing payment...</span>
                  </>
                ) : (
                  <span>[ Pay ₹499 ]</span>
                )}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
