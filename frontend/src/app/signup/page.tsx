"use client";
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Activity, ArrowLeft, Eye, EyeOff, AlertCircle, CheckCircle2,
  User, Stethoscope, ShieldCheck, ChevronDown
} from "lucide-react";
import { signup, SPECIALTY_LABELS, DoctorSpecialty, UserRole } from "@/lib/auth";

const SPECIALTIES = Object.entries(SPECIALTY_LABELS) as [DoctorSpecialty, string][];

export default function SignupPage() {
  const router = useRouter();
  const [role, setRole] = useState<UserRole>("doctor");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [specialty, setSpecialty] = useState<DoctorSpecialty>("intensivist");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    const saved = window.localStorage.getItem("clinical-monitor-theme") as "light"|"dark"|null;
    const t = saved || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.classList.toggle("dark", t === "dark");
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setSuccessMsg("");
    if (!name.trim() || !email.trim() || !password.trim()) { setError("All fields are required."); return; }
    if (password.length < 4) { setError("Password must be at least 4 characters."); return; }
    setLoading(true);
    await new Promise(r => setTimeout(r, 700));
    const result = signup(name.trim(), email.trim(), password, role, role === "doctor" ? specialty : undefined);
    setLoading(false);
    if (!result.success) { setError(result.message); return; }
    setSuccessMsg(result.message);
    if (role === "admin") setTimeout(() => router.push("/login"), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#020617] text-slate-900 dark:text-slate-50 flex items-center justify-center p-6 relative overflow-hidden transition-colors duration-500">
      <Link href="/login" className="fixed top-8 left-8 flex items-center gap-2 text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors font-bold text-sm z-50 uppercase tracking-wider">
        <ArrowLeft size={16} /> Back to Login
      </Link>

      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-indigo-500/20 blur-[120px] rounded-full" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500/20 blur-[120px] rounded-full" />
      </div>

      <motion.div initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.5 }} className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-xl shadow-indigo-600/30 mx-auto mb-5">
            <User size={30} />
          </div>
          <h1 className="text-3xl font-black tracking-tight mb-1">Request Access</h1>
          <p className="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">Ignisia Clinical AI Portal</p>
        </div>

        <AnimatePresence mode="wait">
          {successMsg ? (
            <motion.div key="success" initial={{ opacity:0, scale:0.95 }} animate={{ opacity:1, scale:1 }} className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-2xl border border-emerald-200/60 dark:border-emerald-800/60 p-10 rounded-[2rem] shadow-2xl text-center">
              <CheckCircle2 className="text-emerald-500 mx-auto mb-4" size={48} />
              <h2 className="text-xl font-black mb-3">
                {role === "doctor" ? "Request Sent!" : "Account Created!"}
              </h2>
              <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">{successMsg}</p>
              {role === "doctor" && (
                <Link href="/login" className="mt-6 inline-block px-6 py-3 rounded-xl bg-blue-600 text-white font-black text-sm uppercase tracking-wider hover:bg-blue-700 transition-colors">
                  Back to Login
                </Link>
              )}
            </motion.div>
          ) : (
            <motion.div key="form" className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-2xl border border-slate-200/60 dark:border-slate-800/60 p-8 rounded-[2rem] shadow-2xl relative overflow-hidden">
              <AnimatePresence>
                {loading && (
                  <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
                    className="absolute inset-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur z-20 flex flex-col items-center justify-center rounded-[2rem]">
                    <Activity className="text-indigo-600 animate-pulse mb-3" size={36} />
                    <span className="text-xs font-black uppercase tracking-[0.3em] text-indigo-600 animate-pulse">Submitting…</span>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Role Switcher */}
              <div className="flex gap-2 mb-6 p-1.5 bg-slate-100 dark:bg-slate-800 rounded-2xl">
                {(["doctor","admin"] as UserRole[]).map(r => (
                  <button key={r} onClick={()=>setRole(r)}
                    className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all ${
                      role === r
                        ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                        : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                    }`}>
                    {r === "doctor" ? <Stethoscope size={14}/> : <ShieldCheck size={14}/>}
                    {r === "doctor" ? "Doctor" : "Admin"}
                  </button>
                ))}
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-2">Full Name</label>
                  <input type="text" value={name} onChange={e=>setName(e.target.value)} placeholder="Dr. John Smith"
                    className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all placeholder:text-slate-400" />
                </div>
                <div>
                  <label className="block text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-2">Email</label>
                  <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="doctor@hospital.org"
                    className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all placeholder:text-slate-400" />
                </div>
                <div>
                  <label className="block text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-2">Password</label>
                  <div className="relative">
                    <input type={showPw ? "text" : "password"} value={password} onChange={e=>setPassword(e.target.value)} placeholder="Min. 4 characters"
                      className="w-full pl-4 pr-12 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all placeholder:text-slate-400" />
                    <button type="button" onClick={()=>setShowPw(s=>!s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors">
                      {showPw ? <EyeOff size={16}/> : <Eye size={16}/>}
                    </button>
                  </div>
                </div>

                <AnimatePresence>
                  {role === "doctor" && (
                    <motion.div key="specialty" initial={{ opacity:0, height:0 }} animate={{ opacity:1, height:"auto" }} exit={{ opacity:0, height:0 }}>
                      <label className="block text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-2">Specialty / Department</label>
                      <div className="relative">
                        <select value={specialty} onChange={e=>setSpecialty(e.target.value as DoctorSpecialty)}
                          className="w-full px-4 py-3 pr-10 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all appearance-none cursor-pointer">
                          {SPECIALTIES.map(([k,v]) => <option key={k} value={k}>{v}</option>)}
                        </select>
                        <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                      </div>
                      <p className="mt-2 text-[10px] text-slate-400 dark:text-slate-500 font-medium">
                        You will only see patients relevant to your specialty.
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>

                <AnimatePresence>
                  {error && (
                    <motion.div initial={{ opacity:0, y:-8 }} animate={{ opacity:1, y:0 }} exit={{ opacity:0 }}
                      className="flex items-center gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 text-xs font-bold">
                      <AlertCircle size={14} className="shrink-0" /> {error}
                    </motion.div>
                  )}
                </AnimatePresence>

                <button type="submit" disabled={loading}
                  className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-black uppercase tracking-wider text-sm flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 transition-all">
                  {role === "doctor" ? "Send Access Request" : "Create Admin Account"}
                </button>
              </form>

              <div className="mt-5 pt-5 border-t border-slate-100 dark:border-slate-800 text-center">
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Already have access?{" "}
                  <Link href="/login" className="font-black text-blue-600 hover:underline">Login</Link>
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
