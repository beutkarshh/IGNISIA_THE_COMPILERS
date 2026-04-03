"use client";

import React from "react";
import { AlertTriangle, CheckCircle2, Info, Activity } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface SepsisBannerProps {
  probability: number;
  status: "stable" | "moderate" | "critical";
  lastCheck: string;
}

export function SepsisBanner({ probability, status, lastCheck }: SepsisBannerProps) {
  const isCritical = status === "critical";

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={status}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        className={cn(
          "w-full rounded-[2.5rem] p-8 relative overflow-hidden group transition-all duration-500",
          isCritical 
            ? "bg-rose-600/5 backdrop-blur-xl border border-rose-200/50 shadow-2xl shadow-rose-500/10" 
            : "bg-emerald-600/5 backdrop-blur-xl border border-emerald-200/50 shadow-2xl shadow-emerald-500/10"
        )}
      >
        {/* Animated Background Pulse */}
        <div className={cn(
          "absolute -right-20 -top-20 w-64 h-64 rounded-full opacity-10 blur-3xl",
          isCritical ? "bg-rose-500 group-hover:opacity-20 animate-pulse" : "bg-emerald-500"
        )} />

        <div className="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
          <div className="flex items-center gap-6">
            <div className={cn(
              "w-20 h-20 rounded-[2rem] flex items-center justify-center transition-transform group-hover:scale-110",
              isCritical ? "bg-rose-600 text-white shadow-lg shadow-rose-200" : "bg-emerald-600 text-white shadow-lg shadow-emerald-200"
            )}>
              {isCritical ? <AlertTriangle size={40} strokeWidth={2.5} /> : <CheckCircle2 size={40} strokeWidth={2.5} />}
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                  Primary Risk Assessment
                </span>
                <div className="flex gap-1 items-center px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[8px] font-black uppercase tracking-widest">
                  <Activity size={10} /> Live Ingestion
                </div>
              </div>
              <h1 className={cn(
                "text-4xl font-black tracking-tighter uppercase leading-none",
                isCritical ? "text-rose-600" : "text-emerald-700"
              )}>
                {isCritical ? "Sepsis Risk Detected" : "Stable: Low Risk"}
              </h1>
              <p className="text-sm font-bold text-slate-500 max-w-md leading-relaxed">
                {isCritical 
                  ? "Clinical markers suggest immediate hemodynamic intervention. Elevated lactate and HR detected."
                  : "All clinical markers within normal thresholds. Patient is currently showing signs of recovery."
                }
              </p>
            </div>
          </div>

          <div className="flex items-center gap-8 bg-white/50 p-6 rounded-[2rem] border border-white/20 shadow-sm">
            <div className="text-center space-y-1">
              <div className="flex items-center justify-center gap-1.5 translate-y-1">
                <span className={cn(
                  "text-4xl font-black font-mono tracking-tighter transition-colors",
                  isCritical ? "text-rose-600" : "text-emerald-600"
                )}>
                  {probability}%
                </span>
                <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">Confidence Score</div>
              </div>
              <div className="w-32 h-1.5 bg-slate-100 rounded-full overflow-hidden mt-2">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${probability}%` }}
                  className={cn(
                    "h-full rounded-full transition-all duration-1000",
                    isCritical ? "bg-rose-500" : "bg-emerald-500"
                  )}
                />
              </div>
            </div>

            <div className="h-12 w-px bg-slate-200/60" />
            
            <div className="space-y-1">
              <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">
                Last Clinical Update
              </div>
              <div className="text-xl font-black text-slate-800 tracking-tighter">
                {lastCheck}
              </div>
              <button className="flex items-center gap-1.5 text-[10px] font-black text-blue-600 uppercase tracking-widest hover:text-blue-700 transition-colors">
                <Info size={12} /> View Methodology
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
