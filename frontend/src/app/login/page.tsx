"use client";
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Activity, ArrowLeft, Lock, Eye, EyeOff, AlertCircle, CheckCircle2 } from "lucide-react";
import { login } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [theme, setTheme] = useState<"light"|"dark">("light");

  useEffect(() => {
    const saved = window.localStorage.getItem("clinical-monitor-theme") as "light"|"dark"|null;
    const t = saved || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    setTheme(t);
    document.documentElement.classList.toggle("dark", t === "dark");
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim() || !password.trim()) { setError("Please enter your email and password."); return; }
    setLoading(true);
    await new Promise(r => setTimeout(r, 700));
    const result = login(email.trim(), password);
    setLoading(false);
    if (!result.success) { setError(result.message); return; }
    router.push(result.user?.role === "admin" ? "/dashboard" : "/dashboard");
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#020617] text-slate-900 dark:text-slate-50 flex items-center justify-center p-6 relative overflow-hidden transition-colors duration-500">
      <Link href="/" className="fixed top-8 left-8 flex items-center gap-2 text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors font-bold text-sm z-50 uppercase tracking-wider">
        <ArrowLeft size={16} /> Home
      </Link>

      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-blue-500/20 blur-[120px] rounded-full" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-indigo-500/20 blur-[120px] rounded-full" />
      </div>

      <motion.div initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.5 }} className="w-full max-w-md relative z-10">
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-xl shadow-blue-600/30 mx-auto mb-5">
            <Activity size={30} />
          </div>
          <h1 className="text-3xl font-black tracking-tight mb-1">Secure Login</h1>
          <p className="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">Ignisia Clinical AI</p>
        </div>

        <div className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-2xl border border-slate-200/60 dark:border-slate-800/60 p-8 rounded-[2rem] shadow-2xl relative overflow-hidden">
          <AnimatePresence>
            {loading && (
              <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
                className="absolute inset-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur z-20 flex flex-col items-center justify-center rounded-[2rem]">
                <Activity className="text-blue-600 animate-pulse mb-3" size={36} />
                <span className="text-xs font-black uppercase tracking-[0.3em] text-blue-600 animate-pulse">Authenticating…</span>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-2">Email / User ID</label>
              <input
                type="text" value={email} onChange={e=>setEmail(e.target.value)}
                placeholder="e.g. doctor@ignisia.ai"
                className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all placeholder:text-slate-400"
              />
            </div>
            <div>
              <label className="block text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-2">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"} value={password} onChange={e=>setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-4 pr-12 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all placeholder:text-slate-400"
                />
                <button type="button" onClick={()=>setShowPw(s=>!s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors">
                  {showPw ? <EyeOff size={16}/> : <Eye size={16}/>}
                </button>
              </div>
            </div>

            <AnimatePresence>
              {error && (
                <motion.div initial={{ opacity:0, y:-8 }} animate={{ opacity:1, y:0 }} exit={{ opacity:0 }}
                  className="flex items-center gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 text-xs font-bold">
                  <AlertCircle size={14} className="shrink-0" /> {error}
                </motion.div>
              )}
            </AnimatePresence>

            <button type="submit" disabled={loading}
              className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-black uppercase tracking-wider text-sm flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20 transition-all">
              <Lock size={16} /> Login
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 dark:border-slate-800 text-center">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              New doctor?{" "}
              <Link href="/signup" className="font-black text-blue-600 hover:underline">Request Access</Link>
            </p>
          </div>
        </div>

        <div className="mt-6 p-4 rounded-2xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 text-center mb-2">Demo Credentials</p>
          <div className="flex gap-3">
            <button onClick={()=>{setEmail("admin");setPassword("admin");}} className="flex-1 py-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-300 hover:text-blue-600 transition-colors">Admin</button>
            <button onClick={()=>{setEmail("doctor@ignisia.ai");setPassword("doctor");}} className="flex-1 py-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-300 hover:text-blue-600 transition-colors">Doctor (if approved)</button>
          </div>
        </div>

        <p className="text-center mt-6 text-[10px] font-bold text-slate-400 uppercase tracking-widest">HIPAA & SOC2 Compliant Environment</p>
      </motion.div>
    </div>
  );
}
