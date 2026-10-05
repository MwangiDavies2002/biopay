"use client";
import { useEffect, useState } from "react";
import { request } from "./api";
import { Shell, Icon, WalletCard, Status, Alert, money, remaining, useClock } from "./ui";

export default function Page() {
  const [amount, setAmount] = useState("12500");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [wallet, setWallet] = useState(null);
  const [walletBusy, setWalletBusy] = useState(true);
  const [walletError, setWalletError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const now = useClock();
  const statusOf = p => p.status === "PENDING" && now && Date.parse(p.expiresAt) <= now ? "EXPIRED" : p.status;

  async function loadWallet() {
    setWalletBusy(true); setWalletError("");
    try { setWallet(await request("/wallets/MERCHANT-DEMO-001")); }
    catch (error) { setWalletError(error.message); }
    finally { setWalletBusy(false); }
  }
  useEffect(() => { loadWallet(); }, []);
  useEffect(() => {
    if (!result || result.status !== "PENDING") return;
    let active = true;
    const timer = setInterval(async () => {
      if (Date.parse(result.expiresAt) <= Date.now()) return;
      try {
        const updated = await request(`/payment-requests/${result.id}`);
        if (!active) return;
        setResult(previous => previous?.id === updated.id ? updated : previous);
        setHistory(previous => previous.map(p => p.id === updated.id ? updated : p));
        if (updated.status === "APPROVED") loadWallet();
      } catch { /* The manual refresh action remains available. */ }
    }, 3000);
    return () => { active=false; clearInterval(timer); };
  }, [result?.id, result?.status]);

  async function createPayment(event) {
    event.preventDefault(); setBusy(true); setMessage(""); setCopied(false);
    try {
      if (!amount.trim() || !Number.isFinite(Number(amount)) || Number(amount) < 0.01) throw new Error("Enter an amount of at least KES 0.01.");
      const payment = await request("/payment-requests", {payerUserId:"USER-DEMO-001", merchantId:"MERCHANT-DEMO-001", amount:Number(amount), currency:"KES"});
      setResult(payment); setHistory(previous => [payment, ...previous]);
    } catch (error) { setMessage(error.message); }
    finally { setBusy(false); }
  }
  async function refreshPayment() {
    setBusy(true); setMessage("");
    try {
      const payment=await request(`/payment-requests/${result.id}`);
      setResult(payment); setHistory(previous => previous.map(p => p.id===payment.id ? payment : p));
      await loadWallet();
    } catch (error) { setMessage(error.message); }
    finally { setBusy(false); }
  }
  async function copyId() {
    try { await navigator.clipboard.writeText(result.id); setCopied(true); }
    catch { setMessage("Copy is unavailable in this browser. Select and copy the payment ID below."); }
  }

  return <Shell role="merchant">
    <div className="page-heading"><div><p className="eyebrow">MERCHANT WORKSPACE</p><h1>Payments, without the friction.</h1><p className="subtitle">Create a request. Let your customer take care of the rest.</p></div><span className="pill"><span className="status-dot"/> Demo Merchant</span></div>
    <Alert message={message}/><Alert message={walletError}/>
    <div className="dashboard-grid">
      <div className="stack">
        <section className="panel"><div className="panel-head"><div><h2>Request a payment</h2><p className="subtitle">A simple, secure checkout starts here.</p></div><span className="panel-icon"><Icon name="arrow"/></span></div>
          <form onSubmit={createPayment}><label className="field-label" htmlFor="amount">Payment amount</label><div className="amount-input-wrap"><span className="currency-label">KES</span><input id="amount" name="amount" value={amount} onChange={event=>setAmount(event.target.value)} inputMode="decimal" autoComplete="off" aria-describedby="amount-hint" required/></div><p className="field-hint" id="amount-hint">Enter the amount you want to collect in Kenyan shillings.</p>
            <div className="presets">{[500,1250,5000,12500].map(value=><button type="button" key={value} className={`preset ${Number(amount)===value ? "selected" : ""}`} onClick={()=>setAmount(String(value))}>KES {money(value).replace(/\.00$/,"")}</button>)}</div>
            <div className="detail-box"><div className="detail-row"><span>Customer</span><strong className="avatar-inline"><span className="tiny-avatar">DC</span>Demo Customer</strong></div><div className="detail-row"><span>Payment method</span><strong>Biometric authorization · Demo</strong></div><div className="detail-row"><span>Request validity</span><strong>90 seconds</strong></div></div>
            <button className="primary-button full" type="submit" disabled={busy}>{busy ? <><Icon name="refresh" className="spin"/> Processing…</> : <>Create payment request <Icon name="arrow" size={17}/></>}</button><p className="security-note"><Icon name="shield" size={13}/> Authorization required before funds move</p>
          </form>
        </section>
        {result && <section className="panel result-panel" aria-label="Payment request"><div className="result-header"><h2><Icon name={statusOf(result)==="APPROVED" ? "check" : "link"}/> {statusOf(result)==="APPROVED" ? "Payment received" : "Your payment request"}</h2><Status status={statusOf(result)}/></div><div className="detail-row"><span>Amount to collect</span><strong>KES {money(result.amount)}</strong></div><div className="detail-row"><span>{statusOf(result)==="APPROVED" ? "Payment status" : "Time remaining"}</span><strong>{statusOf(result)==="APPROVED" ? "Funds added to your wallet" : statusOf(result)==="EXPIRED" ? "Create a new request" : remaining(result,now)}</strong></div><p className="field-label" style={{marginTop:20}}>Payment ID</p><div className="id-box"><code>{result.id}</code><button className="icon-button" onClick={copyId} aria-label="Copy payment ID"><Icon name={copied ? "check" : "copy"} size={17}/></button></div><div className="button-row"><a className="primary-button" href={`http://localhost:3001?paymentId=${encodeURIComponent(result.id)}`}><Icon name="link" size={16}/> Open in customer app</a><button className="secondary-button" disabled={busy} onClick={refreshPayment}><Icon name="refresh" size={16}/> Refresh status</button></div><p className="field-hint" role="status">{copied ? "Payment ID copied to your clipboard." : "Share the payment ID with your customer to authorize this request."}</p></section>}
      </div>
      <div className="stack support"><WalletCard wallet={wallet} loading={walletBusy} error={walletError} onRefresh={loadWallet}/><section className="panel"><h2>From request to received.</h2><p className="subtitle">Three steps. One seamless payment.</p><ol className="step-list"><li><span className="step-number current">1</span><div><strong>Create a request</strong><p>Choose an amount and generate a payment ID.</p></div></li><li><span className={`step-number ${result ? "current" : ""}`}>2</span><div><strong>Customer authorizes</strong><p>Your customer reviews the amount and approves in their app.</p></div></li><li><span className={`step-number ${result?.status==="APPROVED" ? "current" : ""}`}>3</span><div><strong>Receive your payment</strong><p>Your wallet updates when the payment is approved.</p></div></li></ol></section><div className="notice"><Icon name="scan" size={20}/><div><strong>Try the full experience</strong>Open the customer app to complete your demo checkout.</div></div></div>
    </div>
    <section className="panel recent-panel"><div className="panel-head" style={{marginBottom:6}}><h2>Recent requests</h2><span className="session-count">{history.length} in this session</span></div>{history.length===0 ? <div className="empty-state"><span className="empty-icon"><Icon name="clock" size={24}/></span><h3>Your next payment starts here.</h3><p>Requests you create in this session will appear here.</p></div> : <div className="recent-list">{history.slice(0,6).map(payment=><div className="recent-row" key={payment.id}><div><strong>KES {money(payment.amount)}</strong><p className="reference">{payment.id}</p></div><Status status={statusOf(payment)}/><button className="text-button" onClick={()=>{setResult(payment);setCopied(false);}}>View request <Icon name="arrow" size={14}/></button></div>)}</div>}</section>
  </Shell>;
}
