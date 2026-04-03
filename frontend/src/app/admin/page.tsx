"use client";
import React, { useState, useEffect, useMemo, useRef } from "react";
import { motion, AnimatePresence, useInView, useMotionValue, useSpring } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Activity, Users, CheckCircle2, XCircle, Bell, ShieldCheck,
  Stethoscope, Sun, SunMoon, LogOut, BarChart2, Monitor,
  Heart, Wind, Droplets, Brain, Bug, TrendingUp, TrendingDown,
  AlertCircle, Zap, ArrowUpRight
} from "lucide-react";
import {
  getAllUsers, getNotifications, approveUser, rejectUser,
  getCurrentUser, logout, SPECIALTY_LABELS,
  type AppUser, type Notification
} from "@/lib/auth";
import { useClinicalData } from "@/hooks/useClinicalData";
import { cn } from "@/lib/utils";

/* ─────────────────────────────────────────────
   Animated Counter Hook
───────────────────────────────────────────── */
function useAnimatedCounter(target: number, duration = 1200) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  useEffect(() => {
    if (!inView) return;
    let start = 0;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start = Math.min(start + step, target);
      setDisplay(Math.round(start));
      if (start >= target) clearInterval(timer);
    }, 16);
    return () => clearInterval(timer);
  }, [inView, target, duration]);
  return { display, ref };
}

/* ─────────────────────────────────────────────
   Animated Counter Component
───────────────────────────────────────────── */
function Counter({ value, className }: { value: number; className?: string }) {
  const { display, ref } = useAnimatedCounter(value);
  return <span ref={ref} className={className}>{display}</span>;
}

/* ─────────────────────────────────────────────
   SVG Radial Progress Ring
───────────────────────────────────────────── */
function RadialRing({ pct, color, size = 120, stroke = 10, children }: {
  pct: number; color: string; size?: number; stroke?: number; children?: React.ReactNode;
}) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const ref = useRef<SVGCircleElement>(null);
  const viewRef = useRef<SVGSVGElement>(null);
  const inView = useInView(viewRef, { once: true });
  const [animated, setAnimated] = useState(false);
  useEffect(() => { if (inView) setTimeout(() => setAnimated(true), 200); }, [inView]);
  const dash = animated ? (pct / 100) * circ : 0;

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg ref={viewRef} width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          strokeWidth={stroke} stroke="currentColor" className="text-slate-100 dark:text-slate-800" />
        <circle ref={ref} cx={size / 2} cy={size / 2} r={r} fill="none"
          strokeWidth={stroke} stroke={color}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
          style={{ transition: "stroke-dasharray 1s cubic-bezier(.4,0,.2,1)" }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {children}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Sparkline
───────────────────────────────────────────── */
function Sparkline({ data, color = "#3b82f6", height = 40 }: {
  data: number[]; color?: string; height?: number;
}) {
  if (data.length < 2) return null;
  const w = 160;
  const min = Math.min(...data);
  const max = Math.max(...data) || 1;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = height - ((v - min) / (max - min + 0.001)) * (height - 4);
    return `${x},${y}`;
  }).join(" ");
  const area = `M0,${height} L${pts.replace(/ /g, " L")} L${w},${height} Z`;
  return (
    <svg viewBox={`0 0 ${w} ${height}`} className="w-full" style={{ height }} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`sg-${color.replace("#","")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#sg-${color.replace("#","")})`} />
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ─────────────────────────────────────────────
   Animated Bar Row
───────────────────────────────────────────── */
function BarRow({ label, value, max, hex, icon: Icon }: {
  label: string; value: number; max: number; hex: string; icon: React.ElementType;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true });
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <motion.div ref={ref} className="group" initial={{ opacity: 0, x: -10 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}>
      <div className="flex items-center gap-3 mb-2">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: `${hex}18` }}>
          <Icon size={13} style={{ color: hex }} />
        </div>
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 flex-1">{label}</span>
        <span className="text-sm font-black" style={{ color: hex }}>{value}</span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
        <motion.div className="h-full rounded-full"
          style={{ background: `linear-gradient(90deg, ${hex}aa, ${hex})` }}
          initial={{ width: "0%" }}
          animate={inView ? { width: `${pct}%` } : { width: "0%" }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1], delay: 0.1 }} />
      </div>
    </motion.div>
  );
}

/* ─────────────────────────────────────────────
   Main Page
───────────────────────────────────────────── */
export default function AdminAnalyticsPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [users, setUsers] = useState<AppUser[]>([]);
  const [notifs, setNotifs] = useState<Notification[]>([]);
  const { patients } = useClinicalData();

  useEffect(() => {
    setMounted(true);
    const user = getCurrentUser();
    if (!user || user.role !== "admin") { router.replace("/login"); return; }
    const saved = window.localStorage.getItem("clinical-monitor-theme") as "light" | "dark" | null;
    const t = saved || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    setTheme(t);
    document.documentElement.classList.toggle("dark", t === "dark");
    refreshData();
  }, []);

  function refreshData() { setUsers(getAllUsers()); setNotifs(getNotifications()); }

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.classList.toggle("dark", next === "dark");
    window.localStorage.setItem("clinical-monitor-theme", next);
  };
  const handleLogout = () => { logout(); router.push("/login"); };
  const handleApprove = (id: string) => { approveUser(id); refreshData(); };
  const handleReject  = (id: string) => { rejectUser(id);  refreshData(); };

  const analytics = useMemo(() => {
    const total    = patients.length;
    const critical = patients.filter(p => p.is_alert).length;
    const stable   = total - critical;
    const cats = [
      { label: "Sepsis",        icon: Bug,      hex: "#f97316", keywords: ["SEPSIS","SEPTIC","INFECTION"] },
      { label: "Cardiac",       icon: Heart,    hex: "#f43f5e", keywords: ["CARDIAC","ARREST","HEART FAILURE","MI","CORONARY"] },
      { label: "Pulmonary",     icon: Wind,     hex: "#0ea5e9", keywords: ["PNEUMONIA","COPD","RESPIRATORY","HYPOXIA","LUNG"] },
      { label: "Renal",         icon: Droplets, hex: "#8b5cf6", keywords: ["RENAL","KIDNEY","AKI"] },
      { label: "Neurological",  icon: Brain,    hex: "#eab308", keywords: ["STROKE","CVA","NEURO","BRAIN","SEIZURE"] },
    ].map(c => ({
      ...c,
      count: patients.filter(p => c.keywords.some(kw => (p.diagnosis || "").toUpperCase().includes(kw))).length,
    }));

    const sparkData = [Math.round(total*0.6), Math.round(total*0.65), Math.round(total*0.7), Math.round(total*0.75), Math.round(total*0.85), Math.round(total*0.92), total];
    return { total, critical, stable, cats, sparkData, critPct: total > 0 ? Math.round((critical / total) * 100) : 0 };
  }, [patients]);

  const doctors        = users.filter(u => u.role === "doctor");
  const approvedDocs   = doctors.filter(d => d.approved);
  const pendingDocs    = doctors.filter(d => !d.approved);
  const pendingNotifs  = notifs.filter(n => n.type === "signup_request");
  const maxCount       = Math.max(...analytics.cats.map(c => c.count), 1);

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#020617] text-slate-900 dark:text-slate-50 transition-colors duration-500 overflow-x-hidden">

      {/* ── Navbar ── */}
      <header className="sticky top-0 z-50 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/60 dark:bg-[#020617]/70 backdrop-blur-2xl">
        <div className="px-6 h-16 flex items-center justify-between">
          {/* Left: logo */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-600/30">
              <Activity size={20} />
            </div>
            <div>
              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Intensive Care Unit</p>
              <h1 className="text-base font-black tracking-tight leading-tight">IGNISIA <span className="text-blue-600">AI</span></h1>
            </div>
          </motion.div>

          {/* Right: 4 controls */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-2">
            {pendingNotifs.length > 0 && (
              <motion.div animate={{ scale: [1, 1.04, 1] }} transition={{ repeat: Infinity, duration: 2 }}
                className="flex items-center gap-1.5 px-3 py-2.5 bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 rounded-2xl text-amber-600 dark:text-amber-400 text-xs font-black">
                <Bell size={13} className="animate-pulse" />
                <span>{pendingNotifs.length} Pending</span>
              </motion.div>
            )}
            <Link href="/dashboard"
              className="flex items-center gap-1.5 px-3 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-xs font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 shadow-sm transition-all hover:shadow-md hover:-translate-y-0.5">
              <Monitor size={14} /> Clinical
            </Link>
            <div className="flex items-center gap-1.5 px-3 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Live Feed</span>
            </div>
            <button onClick={toggleTheme}
              className="w-10 h-10 flex items-center justify-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all hover:-translate-y-0.5">
              {theme === "dark" ? <Sun size={15} className="text-amber-500" /> : <SunMoon size={15} className="text-blue-600" />}
            </button>
            <button onClick={handleLogout}
              className="w-10 h-10 flex items-center justify-center bg-slate-900 dark:bg-white rounded-2xl shadow-sm text-white dark:text-slate-900 hover:opacity-80 transition-all hover:-translate-y-0.5">
              <LogOut size={15} />
            </button>
          </motion.div>
        </div>
      </header>

      {/* ── Hero gradient strip ── */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 via-violet-500/5 to-transparent pointer-events-none" />
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -top-32 right-0 w-96 h-96 bg-violet-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-6 pt-10 pb-6">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-blue-600 dark:text-blue-400 mb-1">Admin Portal</p>
            <h2 className="text-3xl font-black tracking-tight">Analytics <span className="text-blue-600">Command</span> Center</h2>
            <p className="text-sm text-slate-400 dark:text-slate-500 mt-1 font-medium">Real-time ICU intelligence & doctor management</p>
          </motion.div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-6 pb-16 space-y-8">

        {/* ── KPI Cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Total Patients",  value: analytics.total,    icon: Activity,     hex: "#3b82f6", spark: analytics.sparkData, trend: "+2 today", up: true },
            { label: "Critical",        value: analytics.critical,  icon: AlertCircle,  hex: "#f43f5e", spark: analytics.sparkData.map(v=>Math.round(v*0.31)), trend: `${analytics.critPct}% rate`, up: false },
            { label: "Stable",          value: analytics.stable,    icon: Zap,          hex: "#10b981", spark: analytics.sparkData.map(v=>Math.round(v*0.69)), trend: "Improving", up: true },
            { label: "Doctors Active",  value: approvedDocs.length, icon: Users,        hex: "#6366f1", spark: [0,0,1,1,approvedDocs.length,approvedDocs.length,approvedDocs.length], trend: `${pendingDocs.length} pending`, up: true },
          ].map((kpi, i) => (
            <motion.div key={i}
              initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              className="relative p-5 rounded-3xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm hover:shadow-xl hover:shadow-slate-200/50 dark:hover:shadow-black/30 transition-all duration-300 overflow-hidden cursor-default group">

              {/* Glow */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                style={{ background: `radial-gradient(circle at 50% 0%, ${kpi.hex}12, transparent 70%)` }} />
              {/* Top-right icon */}
              <div className="absolute top-4 right-4 w-8 h-8 rounded-xl flex items-center justify-center opacity-10 group-hover:opacity-20 transition-opacity"
                style={{ background: kpi.hex }}>
                <kpi.icon size={16} style={{ color: kpi.hex }} />
              </div>

              <div className="relative z-10">
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-3">{kpi.label}</p>
                <p className="text-5xl font-black mb-2 leading-none" style={{ color: kpi.hex }}>
                  <Counter value={kpi.value} />
                </p>
                <div className="flex items-center gap-1">
                  {kpi.up ? <TrendingUp size={10} style={{ color: kpi.hex }} /> : <TrendingDown size={10} style={{ color: kpi.hex }} />}
                  <span className="text-[9px] font-bold text-slate-400 dark:text-slate-500">{kpi.trend}</span>
                </div>
              </div>

              {/* Sparkline */}
              <div className="mt-4 -mx-1 relative z-10">
                <Sparkline data={kpi.spark} color={kpi.hex} height={40} />
              </div>
            </motion.div>
          ))}
        </div>

        {/* ── Row 2: Radial rings + Condition bars ── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

          {/* ── Status Radials ── */}
          <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-2 p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm hover:shadow-xl transition-shadow duration-500">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-1 h-4 rounded-full bg-blue-600" />
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Patient Status</p>
            </div>

            {/* Big center ring = critical % */}
            <div className="flex flex-col items-center gap-6">
              <RadialRing pct={analytics.critPct} color="#f43f5e" size={160} stroke={16}>
                <p className="text-3xl font-black text-rose-500">{analytics.critPct}%</p>
                <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Critical</p>
              </RadialRing>

              <div className="grid grid-cols-2 gap-4 w-full">
                {[
                  { label: "Critical", value: analytics.critical, pct: analytics.critPct,            color: "#f43f5e" },
                  { label: "Stable",   value: analytics.stable,   pct: 100 - analytics.critPct,      color: "#10b981" },
                ].map((s, i) => (
                  <motion.div key={i} whileHover={{ scale: 1.03 }}
                    className="p-4 rounded-2xl border border-slate-100 dark:border-slate-800 text-center cursor-default"
                    style={{ background: `${s.color}08` }}>
                    <p className="text-2xl font-black" style={{ color: s.color }}>
                      <Counter value={s.value} />
                    </p>
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mt-0.5">{s.label}</p>
                    <p className="text-[9px] font-bold text-slate-300 dark:text-slate-600">{s.pct}%</p>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* ── Condition Bars ── */}
          <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-3 p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm hover:shadow-xl transition-shadow duration-500">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-1 h-4 rounded-full bg-violet-600" />
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Condition Breakdown</p>
            </div>

            {/* Mini radials per condition */}
            <div className="grid grid-cols-5 gap-2 mb-8">
              {analytics.cats.map((cat, i) => {
                const pct = analytics.total > 0 ? Math.round((cat.count / analytics.total) * 100) : 0;
                return (
                  <motion.div key={i} className="flex flex-col items-center gap-1"
                    initial={{ opacity: 0, scale: 0.8 }} whileInView={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.07 }} viewport={{ once: true }}>
                    <RadialRing pct={pct} color={cat.hex} size={64} stroke={7}>
                      <span className="text-[10px] font-black" style={{ color: cat.hex }}>{cat.count}</span>
                    </RadialRing>
                    <p className="text-[8px] font-black uppercase tracking-widest text-slate-400 text-center">{cat.label}</p>
                  </motion.div>
                );
              })}
            </div>

            {/* Bars */}
            <div className="space-y-4">
              {analytics.cats.map((cat, i) => (
                <BarRow key={i} label={cat.label} value={cat.count} max={maxCount} hex={cat.hex} icon={cat.icon} />
              ))}
            </div>
          </motion.div>
        </div>

        {/* ── Row 3: Pending Approvals + Doctors ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Pending Approvals */}
          <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm hover:shadow-xl transition-shadow duration-500">

            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <div className="w-1 h-4 rounded-full bg-amber-500" />
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Pending Approvals</p>
              </div>
              {pendingDocs.length > 0 && (
                <motion.span animate={{ scale: [1, 1.1, 1] }} transition={{ repeat: Infinity, duration: 1.5 }}
                  className="px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400 text-[9px] font-black">
                  {pendingDocs.length} new
                </motion.span>
              )}
            </div>

            <div className="space-y-3">
              <AnimatePresence>
                {pendingDocs.length === 0 && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className="py-12 flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 dark:border-slate-800">
                    <motion.div animate={{ scale: [1, 1.05, 1] }} transition={{ repeat: Infinity, duration: 3 }}>
                      <ShieldCheck size={36} className="text-emerald-400 mb-3" />
                    </motion.div>
                    <p className="text-xs font-black text-slate-400 uppercase tracking-widest">All requests reviewed</p>
                  </motion.div>
                )}
                {pendingDocs.map((doc, i) => (
                  <motion.div key={doc.id} layout
                    initial={{ opacity: 0, x: -16, scale: 0.97 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    exit={{ opacity: 0, x: 16, scale: 0.97 }}
                    transition={{ delay: i * 0.05 }}
                    className="group flex items-center justify-between p-4 rounded-2xl border border-amber-100 dark:border-amber-900/40 bg-gradient-to-r from-amber-50/60 to-transparent dark:from-amber-900/10 hover:border-amber-200 dark:hover:border-amber-800 transition-all">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-2xl bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <Stethoscope size={16} className="text-amber-500" />
                      </div>
                      <div>
                        <p className="text-sm font-black">{doc.name}</p>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{doc.email}</p>
                        {doc.specialty && (
                          <p className="text-[10px] font-black text-blue-500 uppercase tracking-widest">{SPECIALTY_LABELS[doc.specialty]}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}
                        onClick={() => handleApprove(doc.id)}
                        className="w-9 h-9 flex items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 hover:bg-emerald-100 dark:hover:bg-emerald-800/50 transition-colors border border-emerald-100 dark:border-emerald-800">
                        <CheckCircle2 size={15} />
                      </motion.button>
                      <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}
                        onClick={() => handleReject(doc.id)}
                        className="w-9 h-9 flex items-center justify-center rounded-xl bg-rose-50 dark:bg-rose-900/30 text-rose-600 hover:bg-rose-100 dark:hover:bg-rose-800/50 transition-colors border border-rose-100 dark:border-rose-800">
                        <XCircle size={15} />
                      </motion.button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </motion.div>

          {/* Doctors Registry */}
          <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm hover:shadow-xl transition-shadow duration-500">

            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <div className="w-1 h-4 rounded-full bg-blue-600" />
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Registered Doctors</p>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 text-[9px] font-black">
                {approvedDocs.length} active
              </span>
            </div>

            <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
              {approvedDocs.length === 0 && (
                <div className="py-12 flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 dark:border-slate-800">
                  <Users size={36} className="text-slate-300 mb-3" />
                  <p className="text-xs font-black text-slate-400 uppercase tracking-widest">No doctors approved yet</p>
                </div>
              )}
              {approvedDocs.map((doc, i) => (
                <motion.div key={doc.id}
                  initial={{ opacity: 0, y: 8 }} whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }} transition={{ delay: i * 0.04 }}
                  whileHover={{ x: 4 }}
                  className="group flex items-center justify-between p-4 rounded-2xl border border-slate-100 dark:border-slate-800 hover:border-blue-100 dark:hover:border-blue-900/50 hover:bg-blue-50/20 dark:hover:bg-blue-900/10 transition-all cursor-default">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Stethoscope size={15} className="text-blue-500" />
                    </div>
                    <div>
                      <p className="text-sm font-black">{doc.name}</p>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{doc.email}</p>
                    </div>
                  </div>
                  {doc.specialty && (
                    <div className="flex items-center gap-1.5">
                      <span className="text-[9px] font-black uppercase tracking-widest px-2.5 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-800 shrink-0">
                        {SPECIALTY_LABELS[doc.specialty]}
                      </span>
                      <ArrowUpRight size={12} className="text-slate-300 group-hover:text-blue-400 transition-colors" />
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
