"use client";

import React, { useState, useEffect } from "react";
import { PatientSidebar } from "@/components/clinical/PatientSidebar";
import { SepsisBanner } from "@/components/clinical/SepsisBanner";
import { VitalTrend } from "@/components/clinical/VitalTrend";
import { useClinicalStream } from "@/hooks/useClinicalStream";
import { useClinicalData } from "@/hooks/useClinicalData";
import { Activity, Thermometer, Wind, ClipboardList, Database, Zap, SunMoon } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export default function Home() {
  const { patients, isLoading: isLoadingDemographics } = useClinicalData();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window === "undefined") {
      return "light";
    }

    const savedTheme = window.localStorage.getItem("ignisia-theme");
    if (savedTheme === "dark" || savedTheme === "light") {
      return savedTheme;
    }

    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("ignisia-theme", theme);
  }, [theme]);

  const { vitals } = useClinicalStream(patients.map(p => p.subject_id));
  const effectiveSelectedId = selectedId ?? patients[0]?.subject_id ?? null;

  if (isLoadingDemographics || !effectiveSelectedId) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center bg-white dark:bg-slate-950 gap-4 transition-colors duration-300">
         <div className="relative">
            <Activity className="text-blue-600 animate-pulse" size={48} />
            <div className="absolute inset-0 bg-blue-400 blur-2xl opacity-20 animate-pulse" />
         </div>
        <span className="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.4em] animate-pulse">Initializing Relational Database</span>
      </div>
    );
  }

  const selectedPatient = patients.find(p => p.subject_id === effectiveSelectedId)!;
  const currentVitals = vitals[effectiveSelectedId] || [];
  
  const latestPulse = currentVitals.slice(-1)[0];
  const isAlert = latestPulse?.is_outlier || (latestPulse?.valuenum > 130);
  const sepsisProbability = isAlert ? 84 : 12;
  const status = isAlert ? "critical" : "stable";

  const toggleTheme = () => {
    setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"));
  };

  return (
    <main className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden antialiased text-slate-900 dark:text-slate-100 transition-colors duration-300">
      {/* 1. Clinical Rail (Premium Sidebar) */}
      <PatientSidebar 
        patients={patients.map(p => ({
          subject_id: p.subject_id,
          gender: p.gender,
          diagnosis: p.diagnosis,
          bpm: vitals[p.subject_id]?.slice(-1)[0]?.valuenum || 0,
          is_alert: vitals[p.subject_id]?.slice(-1)[0]?.is_outlier || false
        }))} 
        selectedId={effectiveSelectedId} 
        onSelect={setSelectedId} 
      />

      {/* 2. Primary Clinical Workspace */}
      <div className="flex-1 overflow-y-auto px-12 py-10 space-y-10">
        
        {/* Header Branding */}
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-200">
              <Zap size={20} fill="currentColor" />
            </div>
            <div>
              <h2 className="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-none mb-1">Clinic AI Engine</h2>
              <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
                IGNISIA <span className="text-blue-600">CHAOS WARD</span>
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900/80 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-black text-slate-500 dark:text-slate-300 uppercase tracking-widest">Supabase Node: Active</span>
            </div>

            <button
              type="button"
              onClick={toggleTheme}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900/80 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all"
              aria-label="Toggle light and dark mode"
            >
              <SunMoon size={14} className="text-blue-600 dark:text-blue-300" />
              <span className="text-[10px] font-black text-slate-500 dark:text-slate-300 uppercase tracking-widest">Toggle Theme</span>
            </button>
          </div>
        </motion.div>

        {/* Predictive Analytics Section */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="w-full"
        >
          <SepsisBanner 
            probability={sepsisProbability} 
            status={status} 
            lastCheck={new Date().toLocaleTimeString('en-US', { hour12: false })} 
          />
        </motion.section>

        {/* Real-Time Telemetry Grid */}
        <section className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <VitalTrend 
            label="Real-time Heart Rate" 
            unit="BPM" 
            color="#2563EB" 
            data={currentVitals}
            className="xl:col-span-1"
          />
          <VitalTrend 
            label="MAP Integration & Trends" 
            unit="Delta" 
            color="#0EA5E9" 
            data={currentVitals} 
            className="xl:col-span-1"
          />
        </section>

        {/* Clinical History & Patient Case Study */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-slate-900/70 rounded-[3rem] border border-slate-100/50 dark:border-slate-800 shadow-2xl shadow-slate-200/20 dark:shadow-black/20 overflow-hidden transition-colors duration-300"
        >
          <div className="grid grid-cols-1 lg:grid-cols-3">
            {/* Case Identifiers */}
            <div className="lg:col-span-1 p-10 bg-slate-50/50 dark:bg-slate-900/50 border-r border-slate-100 dark:border-slate-800 transition-colors duration-300">
              <div className="flex items-center gap-3 mb-8">
                <div className="w-8 h-8 rounded-lg bg-slate-900 dark:bg-slate-700 text-white flex items-center justify-center transition-colors duration-300">
                  <Database size={16} />
                </div>
                <h3 className="text-sm font-black text-slate-800 dark:text-slate-200 uppercase tracking-tight">Clinical Metadata</h3>
              </div>
              
              <div className="space-y-6">
                {[
                  { label: "Patient Identity", val: `PH-${selectedPatient.subject_id}`, icon: <Activity size={14} className="text-blue-600" />},
                  { label: "Biological Gender", val: selectedPatient.gender, icon: <Thermometer size={14} className="text-rose-500" />},
                  { label: "Admission Type", val: selectedPatient.admission_type, icon: <Wind size={14} className="text-emerald-500" />}
                ].map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center group">
                    <div className="flex items-center gap-2">
                       {item.icon}
                       <span className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">{item.label}</span>
                    </div>
                    <span className="text-sm font-black text-slate-800 dark:text-slate-200 font-mono tracking-tighter">{item.val}</span>
                  </div>
                ))}
              </div>

              <div className="mt-10 p-6 rounded-4xl bg-blue-600 text-white shadow-xl shadow-blue-200">
                 <div className="text-[10px] font-black uppercase tracking-[0.2em] opacity-80 mb-2">Primary Diagnosis</div>
                 <div className="text-xl font-black tracking-tight leading-tight uppercase">
                    {selectedPatient.diagnosis}
                 </div>
              </div>
            </div>

            {/* Protocols & Actions */}
            <div className="lg:col-span-2 p-10 relative">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3 text-slate-800 dark:text-slate-100">
                  <ClipboardList size={20} className="text-blue-600" />
                  <h3 className="text-sm font-black uppercase tracking-tight">Active Clinical Protocols</h3>
                </div>
                <div className="px-3 py-1 bg-blue-50 dark:bg-blue-500/15 text-blue-600 dark:text-blue-300 rounded-lg text-[10px] font-black uppercase tracking-widest transition-colors duration-300">
                  Live Review
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { title: "Fluid Management", desc: "Monitor intake/output every 2 hours.", status: "Active" },
                  { title: "Antibiotic Interval", desc: "Vancomycin administration pending labs.", status: "Pending" },
                  { title: "Respiratory Support", desc: "Patient on 2L Nasal Cannula.", status: "Steady" },
                  { title: "Lab Schedule", desc: "Lactate draw requested for 18:00.", status: "Critical" }
                ].map((protocol, idx) => (
                  <div key={idx} className="p-5 rounded-3xl border border-slate-100 dark:border-slate-800 hover:border-blue-100 dark:hover:border-blue-800/70 hover:bg-blue-50/20 dark:hover:bg-blue-500/10 transition-all group">
                    <div className="flex justify-between items-center mb-1">
                      <h4 className="text-xs font-black text-slate-800 dark:text-slate-100 uppercase">{protocol.title}</h4>
                      <span className={cn(
                        "text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full",
                        protocol.status === "Critical" ? "bg-rose-50 dark:bg-rose-500/15 text-rose-600 dark:text-rose-300" : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-300"
                      )}>{protocol.status}</span>
                    </div>
                    <p className="text-[10px] font-bold text-slate-400 dark:text-slate-500 group-hover:text-slate-500 dark:group-hover:text-slate-400 leading-relaxed uppercase tracking-widest">
                      {protocol.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.section>
      </div>
    </main>
  );
}
