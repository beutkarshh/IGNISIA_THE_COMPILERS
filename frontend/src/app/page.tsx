"use client";
import React, { useState, useEffect, useMemo } from "react";
import { PatientSidebar } from "@/components/clinical/PatientSidebar";
import { SepsisBanner } from "@/components/clinical/SepsisBanner";
import { VitalTrend } from "@/components/clinical/VitalTrend";
import { useClinicalStream } from "@/hooks/useClinicalStream";
import { useClinicalData } from "@/hooks/useClinicalData";
import { Activity, Thermometer, Wind, ClipboardList, Database, Zap, SunMoon, Bed, Sun } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export default function Home() {
  const { patients, isLoading: isLoadingDemographics } = useClinicalData();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [mounted, setMounted] = useState(false);

  // On mount: read saved theme
  useEffect(() => {
    setMounted(true);
    const saved = window.localStorage.getItem("clinical-monitor-theme") as "light" | "dark" | null;
    if (saved) {
      setTheme(saved);
    } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      setTheme("dark");
    }
  }, []);

  // Apply theme to DOM whenever it changes
  useEffect(() => {
    if (!mounted) return;
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    window.localStorage.setItem("clinical-monitor-theme", theme);
  }, [theme, mounted]);

  const { vitals } = useClinicalStream(patients.map(p => p.subject_id));
  const effectiveSelectedId = selectedId ?? patients[0]?.subject_id ?? null;

  const selectedPatient = useMemo(() => {
    return patients.find(p => p.subject_id === effectiveSelectedId);
  }, [patients, effectiveSelectedId]);

  if (isLoadingDemographics || !mounted) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center bg-white dark:bg-slate-950 gap-4 transition-colors duration-500">
         <div className="relative">
            <Activity className="text-blue-600 animate-pulse" size={48} />
            <div className="absolute inset-0 bg-blue-400 blur-2xl opacity-20 animate-pulse" />
         </div>
        <span className="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.4em] animate-pulse">Establishing Secure Stream</span>
      </div>
    );
  }

  if (!selectedPatient) return null;

  const currentVitals = selectedPatient ? (vitals[selectedPatient.subject_id] || []) : [];
  
  // Separate Vitals by ItemID (HR: 211/220045)
  const hrVitals = currentVitals.filter(v => v.itemid === 211 || v.itemid === 220045);
  
  const latestPulse = hrVitals[hrVitals.length - 1];
  // Unified Alert logic: either clinical data flags it, or real-time telemetry is outlier
  const isAlert = selectedPatient.is_alert || latestPulse?.is_outlier || (latestPulse?.valuenum > 130);
  const sepsisProbability = isAlert ? 84 : (selectedPatient?.diagnosis?.toUpperCase().includes("SEPSIS") ? 42 : 12);
  const status = isAlert ? "critical" : (sepsisProbability > 15 ? "moderate" : "stable");

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  // Dynamic bed assignment derived from patient ID
  const bedUnit = `ICU-${String(selectedPatient.subject_id % 6 + 1).padStart(2, "0")}${String.fromCharCode(65 + (selectedPatient.subject_id % 4))}`;

  // Comprehensive dynamic clinical protocols based on diagnosis
  const getProtocols = (diagnosis: string = "") => {
    const d = diagnosis.toUpperCase();

    if (d.includes("SEPSIS") || d.includes("SEPTIC")) return [
      { title: "Fluid Resuscitation", desc: "30 ml/kg crystalloid bolus in first 3 hrs. Reassess at 6 hrs.", status: "Critical" },
      { title: "Broad-Spectrum Antibiotics", desc: "Vancomycin + Piperacillin/Tazobactam Q8H. Culture-guided de-escalation.", status: "Active" },
      { title: "Source Control", desc: "Surgical/radiology consult for drainage or debridement.", status: "Active" },
      { title: "Vasopressors (PRN)", desc: "Norepinephrine target MAP ≥ 65 mmHg. Escalate as needed.", status: "Pending" },
    ];

    if (d.includes("PNEUMONIA")) return [
      { title: "Oxygen Therapy", desc: "Target SpO₂ 92–96% via nasal cannula. Consider HFNC if refractory.", status: "Active" },
      { title: "Antibiotic Coverage", desc: "Azithromycin + Beta-lactam (community); Vanc + Cefepime (HAP).", status: "Active" },
      { title: "Sputum & Blood Cultures", desc: "Awaiting final sensitivity — repeat if no improvement at 48h.", status: "Pending" },
      { title: "Early Mobilization", desc: "Breathing exercises Q4H. Incentive spirometry TID.", status: "Stable" },
    ];

    if (d.includes("ARREST") || d.includes("CARDIAC") || d.includes("HEART FAILURE")) return [
      { title: "Cardiac Monitoring", desc: "Continuous 12-lead ECG. Troponin Q6H × 3.", status: "Critical" },
      { title: "Diuresis", desc: "IV Lasix 40 mg STAT. Target negative fluid balance 1–2 L/24h.", status: "Active" },
      { title: "Cardiology Consult", desc: "Urgent echocardiogram ordered. Hemodynamic optimization.", status: "Active" },
      { title: "Anticoagulation", desc: "Heparin infusion per weight-based protocol. PTT Q6H.", status: "Pending" },
    ];

    if (d.includes("STROKE") || d.includes("CVA") || d.includes("CEREBROVASCULAR")) return [
      { title: "Neurological Monitoring", desc: "NIHSS score Q2H. Pupil checks Q1H.", status: "Critical" },
      { title: "tPA / Thrombectomy", desc: "Within 4.5h window — neurology activating stroke protocol.", status: "Active" },
      { title: "BP Management", desc: "Target < 185/110 mmHg pre-tPA. Labetalol/Nicardipine PRN.", status: "Active" },
      { title: "Stroke Workup", desc: "CT Angiography & Diffusion MRI ordered. Embolic source screen.", status: "Pending" },
    ];

    if (d.includes("GI") || d.includes("BLEED") || d.includes("HEMORRHAGE")) return [
      { title: "Two Large-Bore IV Access", desc: "Active resuscitation in progress. Type & Cross 4 units PRBCs.", status: "Critical" },
      { title: "GI Consult/Endoscopy", desc: "Urgent EGD/colonoscopy for source localization.", status: "Active" },
      { title: "Proton Pump Inhibitor", desc: "Pantoprazole 80 mg IV bolus + 8 mg/hr infusion.", status: "Active" },
      { title: "Hemodynamic Monitoring", desc: "Arterial line placed. MAP target ≥ 65 mmHg.", status: "Pending" },
    ];

    if (d.includes("RENAL") || d.includes("KIDNEY") || d.includes("AKI") || d.includes("FAILURE")) return [
      { title: "Fluid Balance", desc: "Strict I/O monitoring. Restrict IV fluids if fluid-overloaded.", status: "Active" },
      { title: "Nephrotoxin Avoidance", desc: "Hold NSAIDs, aminoglycosides, IV contrast. Review all meds.", status: "Active" },
      { title: "Dialysis Assessment", desc: "Nephrology consult placed. CRRT initiation criteria under review.", status: "Pending" },
      { title: "Electrolyte Correction", desc: "Treat hyperkalemia per protocol. Kayexalate PRN.", status: "Stable" },
    ];

    if (d.includes("COPD") || d.includes("RESPIRATORY") || d.includes("HYPOXIA")) return [
      { title: "Bronchodilators", desc: "Albuterol + Ipratropium Q4H nebulizers. Titrate to response.", status: "Active" },
      { title: "NIV / BiPAP", desc: "Non-invasive ventilation initiated. IPAP 14 / EPAP 5.", status: "Active" },
      { title: "Systemic Steroids", desc: "Methylprednisolone 125 mg IV Q8H × 3 days.", status: "Stable" },
      { title: "Intubation Readiness", desc: "Respiratory threshold met — anesthesia on standby.", status: "Pending" },
    ];

    if (d.includes("HYPERTENSION") || d.includes("HYPOTENSION")) return [
      { title: "BP Monitoring", desc: "Arterial line placed. Auto-cycling NIBP Q15 min.", status: "Active" },
      { title: "Vasopressor / Anti-hypertensive", desc: "Norepinephrine/Labetalol titrated to MAP target.", status: "Active" },
      { title: "End-Organ Assessment", desc: "Creatinine, troponin, lactate Q6H. Fundoscopy if hypertensive.", status: "Pending" },
      { title: "Euvolemia Target", desc: "Fluid resuscitation vs. diuresis based on fluid status.", status: "Stable" },
    ];

    if (d.includes("OVERDOSE") || d.includes("TOXIC") || d.includes("INGESTION")) return [
      { title: "Toxicology Consult", desc: "Poison Control notified. Toxscreen pending.", status: "Critical" },
      { title: "GI Decontamination", desc: "Activated charcoal if < 1h post-ingestion and airway intact.", status: "Active" },
      { title: "Antidote Administration", desc: "N-acetylcysteine / Naloxone per substance protocol.", status: "Active" },
      { title: "Renal/Hepatic Support", desc: "LFTs, UDS, and metabolic panel Q6H. Dialysis PRN.", status: "Pending" },
    ];

    // Default general ICU monitoring
    return [
      { title: "Vital Sign Monitoring", desc: "Q2H documentation. Continuous pulse oximetry.", status: "Active" },
      { title: "DVT Prophylaxis", desc: "Enoxaparin 40 mg SQ daily. Sequential compression device active.", status: "Active" },
      { title: "Fall & Pressure Injury Prevention", desc: "Hourly repositioning. Foam mattress overlay applied.", status: "Active" },
      { title: "Nutrition Assessment", desc: "Dietitian consult placed. Enteral nutrition goal 25 kcal/kg/day.", status: "Pending" },
    ];
  };

  const protocols = getProtocols(selectedPatient?.diagnosis);

  return (
    <main className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden antialiased text-slate-900 dark:text-slate-100 transition-colors duration-500">
      {/* 1. Clinical Rail */}
      <PatientSidebar 
        patients={patients.map(p => ({
          subject_id: p.subject_id,
          gender: p.gender,
          diagnosis: p.diagnosis,
          bpm: vitals[p.subject_id]?.slice(-1)[0]?.valuenum || p.bpm || 0,
          is_alert: p.is_alert || vitals[p.subject_id]?.slice(-1)[0]?.is_outlier || (vitals[p.subject_id]?.slice(-1)[0]?.valuenum > 130)
        }))} 
        selectedId={effectiveSelectedId!} 
        onSelect={setSelectedId} 
      />

      {/* 2. Primary Clinical Workspace */}
      <div className="flex-1 overflow-y-auto px-12 py-10 space-y-8 custom-scrollbar">
        
        {/* Dynamic Header Information */}
        <motion.div 
          key={selectedPatient.subject_id}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-xl shadow-blue-500/20">
                <Zap size={24} fill="currentColor" />
              </div>
              <div>
                <h2 className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] leading-none mb-1.5">Intensive Care Unit</h2>
                <h1 className="text-2xl font-black tracking-tight flex items-center gap-2">
                  PATIENT <span className="text-blue-600">MONITOR</span>
                </h1>
              </div>
            </div>

            <div className="h-10 w-px bg-slate-200 dark:bg-slate-800 mx-2" />

            <div className="flex items-center gap-8">
               <div>
                  <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Patient ID</p>
                  <p className="text-sm font-black text-slate-900 dark:text-slate-100 font-mono">PH-{selectedPatient.subject_id}</p>
               </div>
               <div>
                  <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Gender</p>
                  <p className="text-sm font-black text-slate-900 dark:text-slate-100">{selectedPatient.gender === "M" ? "MALE" : "FEMALE"}</p>
               </div>
               <div>
                  <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Bed Assignment</p>
                  <p className="text-sm font-black text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                    <Bed size={14} className="text-blue-600" />
                    {bedUnit}
                  </p>
               </div>
               <div>
                  <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Status</p>
                  <p className={cn(
                    "text-sm font-black uppercase",
                    isAlert ? "text-rose-600" : "text-emerald-600"
                  )}>{isAlert ? "CRITICAL" : "STABLE"}</p>
               </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl shadow-sm">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Live Feed</span>
            </div>

            {/* Icon-only theme toggle */}
            <button
              type="button"
              onClick={toggleTheme}
              title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
              className="w-10 h-10 flex items-center justify-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all text-slate-600 dark:text-slate-300"
            >
              {theme === "dark" ? <Sun size={16} className="text-amber-500" /> : <SunMoon size={16} className="text-blue-600" />}
            </button>
          </div>
        </motion.div>

        {/* Predictive Analytics Section */}
        <motion.section 
          key={`banner-${selectedPatient.subject_id}`}
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="w-full"
        >
          <SepsisBanner 
            probability={sepsisProbability} 
            status={status} 
            lastCheck={new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })} 
          />
        </motion.section>

        {/* Real-Time Telemetry Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <VitalTrend 
            label="Heart Rate Telemetry" 
            unit="BPM" 
            color="#2563EB" 
            data={currentVitals.filter(v => [211, 220045].includes(v.itemid))}
            className="shadow-xl shadow-blue-500/5"
          />
          <VitalTrend 
            label="MAP Trends" 
            unit="mmHg" 
            color="#0891B2" 
            data={currentVitals.filter(v => [456, 52, 6702, 443, 220052, 220181, 225312].includes(v.itemid))} 
          />
        </div>

        {/* Clinical Case Explorer */}
        <motion.section 
          key={`profile-${selectedPatient.subject_id}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-100 dark:border-slate-800 shadow-2xl shadow-slate-200/20 dark:shadow-black/40 overflow-hidden"
        >
          <div className="grid grid-cols-1 lg:grid-cols-3 divide-x divide-slate-100 dark:divide-slate-800">
            {/* Metadata Panel */}
            <div className="p-10 bg-slate-50/50 dark:bg-slate-900/50">
              <div className="flex items-center gap-3 mb-8">
                <div className="w-8 h-8 rounded-lg bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 flex items-center justify-center">
                  <Database size={16} />
                </div>
                <h3 className="text-sm font-black text-slate-800 dark:text-slate-100 uppercase tracking-tight">Clinical Profile</h3>
              </div>
              
              <div className="space-y-6">
                {[
                  { label: "Admission Type", val: selectedPatient.admission_type || "N/A", icon: <Activity size={14} className="text-blue-600" />},
                  { label: "Insurance Tier", val: selectedPatient.insurance || "N/A", icon: <Thermometer size={14} className="text-rose-500" />},
                  { label: "Language", val: selectedPatient.language || "EN-US", icon: <Wind size={14} className="text-emerald-500" />}
                ].map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                       {item.icon}
                       <span className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">{item.label}</span>
                    </div>
                    <span className="text-sm font-black text-slate-800 dark:text-slate-200 font-mono uppercase tracking-tighter">{item.val}</span>
                  </div>
                ))}
              </div>

              <div className={cn(
                "mt-10 p-6 rounded-3xl text-white shadow-xl ring-4",
                isAlert
                  ? "bg-rose-600 shadow-rose-500/20 ring-rose-600/10"
                  : "bg-blue-600 shadow-blue-500/20 ring-blue-600/10"
              )}>
                 <div className="text-[10px] font-black uppercase tracking-[0.2em] opacity-80 mb-2">Primary Diagnosis</div>
                 <div className="text-lg font-black tracking-tight leading-tight uppercase">
                    {selectedPatient.diagnosis || "CLINICAL EVALUATION"}
                 </div>
              </div>
            </div>

            {/* Protocol Panel */}
            <div className="lg:col-span-2 p-10 relative">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3 text-slate-800 dark:text-slate-100">
                  <ClipboardList size={20} className="text-blue-600" />
                  <h3 className="text-sm font-black uppercase tracking-tight">Active Clinical Protocols</h3>
                </div>
                <div className={cn(
                  "px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest",
                  isAlert ? "bg-rose-50 dark:bg-rose-900/50 text-rose-600" : "bg-blue-50 dark:bg-blue-900/50 text-blue-600"
                )}>
                  {isAlert ? "⚠ Urgent" : "Live Sync"}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {protocols.map((protocol, idx) => (
                  <div key={idx} className="p-6 rounded-[2rem] border border-slate-100 dark:border-slate-800 hover:border-blue-200 dark:hover:border-blue-900 hover:bg-blue-50/20 dark:hover:bg-blue-900/20 transition-all group">
                    <div className="flex justify-between items-center mb-1.5">
                      <h4 className="text-xs font-black text-slate-800 dark:text-slate-100 uppercase">{protocol.title}</h4>
                      <span className={cn(
                        "text-[8px] font-black uppercase tracking-widest px-2.5 py-1 rounded-lg",
                        protocol.status === "Critical" ? "bg-rose-100 text-rose-600 animate-pulse" : 
                        protocol.status === "Pending" ? "bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400" :
                        "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                      )}>{protocol.status}</span>
                    </div>
                    <p className="text-[10px] font-bold text-slate-400 dark:text-slate-500 group-hover:text-slate-500 dark:group-hover:text-slate-400 leading-relaxed uppercase tracking-wider">
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
