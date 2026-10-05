"use client";
import { useEffect, useState } from "react";

const paths = {
  grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  wallet: "M3 6h17v14H3z M3 6V4h14v2 M16 11h5v5h-5z",
  arrow: "M5 12h14 M13 6l6 6-6 6",
  check: "M5 12l4 4L19 6",
  copy: "M9 9h12v12H9z M15 9V3H3v12h6",
  refresh: "M20 7v5h-5 M4 17v-5h5 M5 8a8 8 0 0113-3l2 2 M19 16a8 8 0 01-13 3l-2-2",
  shield: "M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6z M8 12l3 3 5-6",
  code: "M8 7l-5 5 5 5 M16 7l5 5-5 5 M14 4l-4 16",
  scan: "M3 8V3h5 M16 3h5v5 M21 16v5h-5 M8 21H3v-5 M8 15v-4a4 4 0 018 0v3 M11 17v-6a1 1 0 012 0v7 M8 18v-1 M16 17v1",
  clock: "M12 3a9 9 0 100 18 9 9 0 000-18 M12 7v5l3 2",
  close: "M6 6l12 12 M18 6L6 18",
  link: "M14 3h7v7 M21 3L10 14 M10 3H3v18h18v-7",
  user: "M12 3a4 4 0 100 8 4 4 0 000-8 M4 21v-3a8 8 0 0116 0v3",
};
export function Icon({name, size=20, ...props}) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}><path d={paths[name] || paths.grid}/></svg>;
}
const links = [
  ["merchant", "Merchant", "grid", "http://localhost:3000"],
  ["customer", "Customer", "wallet", "http://localhost:3001"],
  ["api", "Payment API", "code", "http://localhost:8080"],
  ["risk", "Risk explorer", "shield", "http://localhost:8000/docs"],
];
export function Shell({role, children}) {
  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to content</a>
    <aside className="sidebar">
      <a className="brand" href={role === "customer" ? "http://localhost:3001" : "http://localhost:3000"}><span className="brand-mark"><Icon name="scan" size={26}/></span>BioPay<span className="brand-dot">.</span></a>
      <div className="workspace"><span className="workspace-avatar">B</span><div><strong>Demo workspace</strong><small>Local payment network</small></div><span className="status-dot"/></div>
      <p className="nav-label">WORKSPACE</p>
      <nav aria-label="Workspace navigation">{links.map(([id, label, icon, href]) => <a key={id} href={href} className={role===id ? "nav-link active" : "nav-link"} aria-current={role===id ? "page" : undefined}><Icon name={icon}/>{label}{role===id && <span className="nav-active-dot"/>}</a>)}</nav>
      <div className="sidebar-bottom"><div className="demo-label"><span className="status-dot"/> Demo environment</div><p>Explore payments with simulated authorization.</p><div className="profile"><span className="profile-avatar"><Icon name={role==="customer" ? "user" : "grid"}/></span><div><strong>{role==="customer" ? "Demo Customer" : "Demo Merchant"}</strong><small>{role==="customer" ? "Personal account" : "Merchant account"}</small></div></div></div>
    </aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumb">Workspace <span>/</span> <strong>{role==="customer" ? "Customer" : "Merchant"}</strong></div><div className="topbar-right"><span className="network-label"><span className="status-dot"/> Local network</span><span className="avatar">{role==="customer" ? "DC" : "DM"}</span></div></header><main id="main" className="page-content">{children}<footer className="page-footer"><span>BioPay · Payments, made personal.</span><span>Local demo · KES</span></footer></main></div>
  </div>;
}
export const money = value => new Intl.NumberFormat("en-KE", {minimumFractionDigits:2, maximumFractionDigits:4}).format(Number(value));
export function Status({status}) {
  const labels = {PENDING:"Awaiting approval", APPROVED:"Approved", EXPIRED:"Expired"};
  return <span className={`status-badge status-${String(status).toLowerCase()}`}><span/>{labels[status] || status}</span>;
}
export function useClock() {
  const [now, setNow] = useState(null);
  useEffect(() => { setNow(Date.now()); const timer=setInterval(()=>setNow(Date.now()),1000); return ()=>clearInterval(timer); },[]);
  return now;
}
export function remaining(payment, now) {
  if (!now || !payment?.expiresAt) return "…";
  const seconds=Math.max(0, Math.ceil((Date.parse(payment.expiresAt)-now)/1000));
  return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,"0")}`;
}
export function Alert({message, tone="error"}) {
  if (!message) return null;
  return <div className={`alert alert-${tone}`} role={tone==="error" ? "alert" : "status"}><Icon name={tone==="success" ? "check" : "shield"}/><span>{message}</span></div>;
}
export function WalletCard({wallet, loading, error, onRefresh, personal=false}) {
  return <section className="wallet-card" aria-label="Wallet balance"><div className="wallet-top"><span><Icon name="wallet"/> {personal ? "Your wallet" : "Merchant wallet"}</span><button className="icon-button on-dark" onClick={onRefresh} disabled={loading} aria-label="Refresh wallet balance"><Icon name="refresh" className={loading ? "spin" : ""}/></button></div><div className="wallet-label">Available balance</div><div className="wallet-amount"><span>KES</span> {wallet ? money(wallet.balance) : "—"}</div><div className="wallet-bottom"><span><span className="status-dot"/> {error ? "Refresh to reconnect" : loading ? "Updating balance…" : wallet ? "Balance up to date" : "Loading wallet…"}</span><span>Kenyan shilling</span></div></section>;
}
