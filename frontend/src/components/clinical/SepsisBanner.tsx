"use client";

import React from "react";
import { AlertTriangle, ShieldCheck, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface SepsisBannerProps {
  probability: number;
  status: "stable" | "moderate" | "critical";
  lastCheck: string;
}

export function SepsisBanner({ probability, status, lastCheck }: SepsisBannerProps) {
  const isCritical = status === "critical";
  const isModerate = status === "moderate";

  return (
    <div className={cn(
      "w-full p-6 rounded-3xl border transition-all duration-500 flex items-center justify-between shadow-2xl shadow-slate-200/50",
      isCritical ? "bg-rose-50 border-rose-200 text-rose-900" : 
      isModerate ? "bg-amber-50 border-amber-200 text-amber-900" : 
      "bg-emerald-50 border-emerald-200 text-emerald-900"
    )}>
      <div className="flex items-center gap-6">
        <div className={cn(
          "w-16 h-16 rounded-2xl flex items-center justify-center transition-all",
          isCritical ? "bg-rose-600 text-white animate-pulse" : 
          isModerate ? "bg-amber-500 text-white" : 
          "bg-emerald-600 text-white"
        )}>
          {isCritical ? <AlertTriangle size={32} /> : isModerate ? <Activity size={32} /> : <ShieldCheck size={32} />}
        </div>

        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-black uppercase tracking-[0.2em] opacity-60">Primary Risk Assessment</span>
            <span className="w-1 h-1 rounded-full bg-current opacity-40"></span>
            <span className="text-xs font-bold font-mono opacity-60 uppercase">Updated {lastCheck}</span>
          </div>
          <h1 className="text-4xl font-black tracking-tighter uppercase">
            {isCritical ? "CRITICAL: SEPSIS ONSET DETECTED" : 
             isModerate ? "MODERATE RISK: MONITORING VITALS" : 
             "LOW RISK: STABLE RECOVERY"}
          </h1>
          <p className="text-sm font-medium opacity-70 mt-1 max-w-xl">
            {isCritical ? "System detects significant lactate spikes and dropping MAP. Recommend immediate clinical intervention and antibiotic administration." : 
             isModerate ? "Minor deviation in heart rate and temperature detected. Continue automatic monitoring for the next 2 hours." : 
             "All clinical markers within normal thresholds. Patient is currently stable and showing signs of recovery."}
          </p>
        </div>
      </div>

      <div className="text-right">
        <div className="text-7xl font-black font-mono tracking-tighter leading-none mb-1">
          {probability}%
        </div>
        <div className="text-xs font-black uppercase tracking-widest opacity-60">
          Confidence Score
        </div>
      </div>
    </div>
  );
}
