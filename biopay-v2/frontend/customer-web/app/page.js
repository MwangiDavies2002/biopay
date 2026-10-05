"use client";
import { useEffect, useState } from "react";
import { request } from "./api";
import { Shell, Icon, WalletCard, Status, Alert, money, remaining, useClock } from "./ui";

const validId = id => /^PAY-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
export default function Page() {
  const [paymentId, setPaymentId] = useState("");
  const [payment, setPayment] = useState(null);
  const [wallet, setWallet] = useState(null);
  const [walletBusy, setWalletBusy] = useState(true);
  const [walletError, setWalletError] = useState("");
  const [message, setMessage] = useState("");
  const [tone, setTone] = useState("error");
  const [busy, setBusy] = useState(false);
  const now = useClock();
  const expired = payment?.status === "EXPIRED" || (payment?.status === "PENDING" && now && Date.parse(payment.expiresAt) <= now);
  const status = expired ? "EXPIRED" : payment?.status;

  async function loadWallet() {
    setWalletBusy(true); setWalletError("");
    try { setWallet(await request("/wallets/USER-DEMO-001")); }
    catch (error) { setWalletError(error.message); }
    finally { setWalletBusy(false); }
  }
  async function loadPayment(event, initialId) {
    event?.preventDefault(); setBusy(true); setMessage(""); setPayment(null);
    try {
      const id = (initialId || paymentId).trim();
      if (!validId(id)) throw new Error("Paste a valid payment ID from the merchant app.");
      const result = await request(`/payment-requests/${encodeURIComponent(id)}`);
      if (result.payerUserId !== "USER-DEMO-001") throw new Error("This payment belongs to a different customer.");
      setPayment(result);
    } catch (error) { setTone("error"); setMessage(error.message); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    loadWallet();
    const id=new URLSearchParams(window.location.search).get("paymentId");
    if (id) { setPaymentId(id); loadPayment(null,id); }
  }, []);

  async function authorize() {
    if (!payment || payment.status!=="PENDING" || expired) return;
    setBusy(true); setTone("info"); setMessage("Authorizing your demo payment…");
    try {
      const approved = await request(`/payment-requests/${encodeURIComponent(payment.id)}/demo-authorize`, {deviceId:"DEVICE-DEMO-001", liveness:true});
      setPayment(approved); setTone("success"); setMessage(`Payment of KES ${money(approved.amount)} approved. You're all set.`);
      await loadWallet();
    } catch (error) { setTone("error"); setMessage(error.message); }
    finally { setBusy(false); }
  }

  return <Shell role="customer"><div className="page-heading"><div><p className="eyebrow">CUSTOMER WORKSPACE</p><h1>Your wallet. Your approval.</h1><p className="subtitle">Review every payment and stay in control of your money.</p></div><span className="pill"><span className="status-dot"/> Demo Customer</span></div>
    <Alert message={message} tone={tone}/><Alert message={walletError}/>
    <div className="dashboard-grid"><div className="stack"><section className="panel"><div className="panel-head"><div><h2>Review a payment</h2><p className="subtitle">Enter the payment ID shared by your merchant.</p></div><span className="panel-icon"><Icon name="scan"/></span></div><form onSubmit={loadPayment}><label className="field-label" htmlFor="payment-id">Payment ID</label><div className="input-row"><input id="payment-id" className="input input-id" value={paymentId} onChange={event=>{setPaymentId(event.target.value);setPayment(null);setMessage("");}} placeholder="PAY-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" autoComplete="off" spellCheck="false" required aria-describedby="payment-id-hint" disabled={busy}/><button className="primary-button" disabled={busy} type="submit">{busy ? <Icon name="refresh" className="spin" size={16}/> : <Icon name="arrow" size={16}/>} {busy ? "Please wait…" : "Find payment"}</button></div><p className="field-hint" id="payment-id-hint">Your merchant can also send you a link that opens the payment directly.</p></form>
      {payment ? <div><div className="payment-summary"><span className="summary-icon"><Icon name={status==="APPROVED" ? "check" : "grid"} size={26}/></span><p>{status==="APPROVED" ? "You've paid Demo Merchant" : "Payment to Demo Merchant"}</p><div className="amount-display"><small>{payment.currency}</small>{money(payment.amount)}</div><Status status={status}/></div><div className="detail-box"><div className="detail-row"><span>Merchant</span><strong>Demo Merchant</strong></div><div className="detail-row"><span>From</span><strong>Your KES wallet</strong></div><div className="detail-row"><span>Amount</span><strong>KES {money(payment.amount)}</strong></div><div className="detail-row"><span>{status==="APPROVED" ? "Status" : "Time remaining"}</span><strong>{status==="APPROVED" ? "Payment complete" : expired ? "This request has expired" : remaining(payment,now)}</strong></div></div>
        {status==="PENDING" && <><button className="primary-button full" onClick={authorize} disabled={busy}><Icon name="scan" size={19}/>{busy ? "Authorizing…" : `Approve KES ${money(payment.amount)} · Demo`}</button><p className="security-note"><Icon name="shield" size={13}/> Simulated biometric and liveness authorization</p></>}
        {expired && <div className="notice" style={{marginTop:20}}><Icon name="clock"/><div><strong>This request has expired</strong>Ask your merchant to create a new payment request.</div></div>}
        {status==="APPROVED" && <div className="notice" style={{marginTop:20}}><Icon name="check"/><div><strong>Payment complete</strong>Your balance has been refreshed. You're ready for your next payment.</div></div>}
        <p className="field-hint" style={{marginTop:16,overflowWrap:"anywhere"}}>Reference: {payment.id}</p>
      </div> : <div className="empty-state" style={{paddingTop:42,paddingBottom:26}}><span className="empty-icon"><Icon name="scan" size={25}/></span><h3>Ready when you are.</h3><p>Find a payment to see the merchant, amount,<br/>and authorization details before you approve.</p></div>}
    </section></div><div className="stack support"><WalletCard personal wallet={wallet} loading={walletBusy} error={walletError} onRefresh={loadWallet}/><section className="panel"><h2>You're in control.</h2><p className="subtitle">Your approval makes the difference.</p><ol className="step-list"><li><span className="step-number current">1</span><div><strong>Find your payment</strong><p>Paste the ID or open a link from your merchant.</p></div></li><li><span className={`step-number ${payment ? "current" : ""}`}>2</span><div><strong>Review the details</strong><p>Check the merchant and amount before you continue.</p></div></li><li><span className={`step-number ${status==="APPROVED" ? "current" : ""}`}>3</span><div><strong>Approve your payment</strong><p>Authorize once. Your wallet updates automatically.</p></div></li></ol></section><div className="notice"><Icon name="shield"/><div><strong>No surprise payments</strong>Funds move only after successful authorization. Requests expire after 90 seconds.</div></div></div></div>
  </Shell>;
}
