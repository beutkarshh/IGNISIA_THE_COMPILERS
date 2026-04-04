"use client";
import React, { useState, useEffect, useMemo } from "react";
import { PatientSidebar } from "@/components/clinical/PatientSidebar";
import { SepsisBanner } from "@/components/clinical/SepsisBanner";
import { VitalTrend } from "@/components/clinical/VitalTrend";
import { useClinicalStream } from "@/hooks/useClinicalStream";
import { useClinicalData } from "@/hooks/useClinicalData";
import {
  Activity, Thermometer, Wind, ClipboardList, Database, Zap,
  SunMoon, Bed, Sun, LogOut, BarChart2, Brain, Loader2, AlertTriangle,
  FileText, Clock, X, Heart
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ShiftHandoverReport from "@/components/clinical/ShiftHandoverReport";
import FamilyCommunicationPanel from "@/components/clinical/FamilyCommunicationPanel";
import AIAnalysisPanel from "@/components/clinical/AIAnalysisPanel";
import {
  getCurrentUser, logout, getNotifications, canDoctorSeePatient,
  SPECIALTY_LABELS, type AppUser
} from "@/lib/auth";
import {
  assessMIMICPatient, type AssessmentResponse, formatErrorMessage, isNetworkError
} from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const { patients, isLoading: isLoadingDemographics } = useClinicalData();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [mounted, setMounted] = useState(false);
  const [currentUser, setCurrentUser] = useState<AppUser | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastTelemetryAt, setLastTelemetryAt] = useState<Date | null>(null);
  const [syncSecondsAgo, setSyncSecondsAgo] = useState<number | null>(null);
  
  // Assessment state
  const [assessmentLoading, setAssessmentLoading] = useState(false);
  const [currentAssessment, setCurrentAssessment] = useState<AssessmentResponse | null>(null);
  const [assessmentError, setAssessmentError] = useState<string | null>(null);
  const [assessmentHistory, setAssessmentHistory] = useState<Record<number, AssessmentResponse>>({});
  
  // Shift handover report state
  const [showHandoverReport, setShowHandoverReport] = useState(false);
  
  // Dashboard tab state
  const [activeTab, setActiveTab] = useState<"monitoring" | "ai" | "family">("ai");

  useEffect(() => {
    setMounted(true);
    const user = getCurrentUser();
    if (!user) { router.replace("/login"); return; }
    setCurrentUser(user);
    const saved = window.localStorage.getItem("clinical-monitor-theme") as "light" | "dark" | null;
    const t = saved || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    setTheme(t);
    document.documentElement.classList.toggle("dark", t === "dark");
    if (user.role === "admin") {
      setPendingCount(getNotifications().filter(n => n.type === "signup_request").length);
    }
  }, []);

  useEffect(() => {
    if (!mounted) return;
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("clinical-monitor-theme", theme);
  }, [theme, mounted]);

  const toggleTheme = () => setTheme(prev => prev === "dark" ? "light" : "dark");
  const handleLogout = () => { logout(); router.push("/login"); };

  // All hooks must be called before any conditional returns - fix order
  const visiblePatients = useMemo(() => {
    if (!currentUser) return patients;
    if (currentUser.role === "admin") return patients;
    return patients.filter(p => canDoctorSeePatient(currentUser.specialty || "intensivist", p.diagnosis || ""));
  }, [patients, currentUser]);

  // Get vitals data for all patients - this must be called before any conditional returns
  const { vitals } = useClinicalStream(patients.map(p => p.subject_id));
  const effectiveSelectedId = selectedId ?? visiblePatients[0]?.subject_id ?? null;

  // Load cached assessment when patient changes
  useEffect(() => {
    if (effectiveSelectedId && assessmentHistory[effectiveSelectedId]) {
      setCurrentAssessment(assessmentHistory[effectiveSelectedId]);
    } else {
      setCurrentAssessment(null);
    }
    setAssessmentError(null);
  }, [effectiveSelectedId, assessmentHistory]);

  const selectedPatient = useMemo(
    () => visiblePatients.find(p => p.subject_id === effectiveSelectedId),
    [visiblePatients, effectiveSelectedId]
  );

  // Get current vitals for selected patient
  const currentVitals = selectedPatient ? (vitals[selectedPatient.subject_id] || []) : [];

  // Debug logging to see if data is reaching the component
  useEffect(() => {
    if (selectedPatient && currentVitals.length > 0) {
      console.log(`[Dashboard Debug] Patient ${selectedPatient.subject_id} has ${currentVitals.length} vital readings`);
      
      // Log all unique itemids we have
      const uniqueItemids = [...new Set(currentVitals.map(v => v.itemid))];
      console.log(`[Dashboard Debug] Available itemids:`, uniqueItemids);
      
      // Check heart rate data
      const hrData = currentVitals.filter(v => [211, 220045].includes(v.itemid));
      const mapData = currentVitals.filter(v => [456, 52, 6702, 443, 220052, 220181, 225312].includes(v.itemid));
      
      console.log(`[Dashboard Debug] HR data: ${hrData.length} points`, hrData.slice(0, 2));
      console.log(`[Dashboard Debug] MAP data: ${mapData.length} points`, mapData.slice(0, 2));
      
      // Log a few sample records to check structure
      console.log(`[Dashboard Debug] Sample vitals structure:`, currentVitals.slice(0, 2));
    } else if (selectedPatient) {
      console.log(`[Dashboard Debug] No vital data for patient ${selectedPatient.subject_id}`);
    }
  }, [currentVitals, selectedPatient]);

  // Assessment functions
  const runAssessment = async () => {
    if (!selectedPatient) return;
    
    setAssessmentLoading(true);
    setAssessmentError(null);
    
    try {
      // Pass subject_id as string - the API client will handle the URL properly
      const response = await assessMIMICPatient(selectedPatient.subject_id.toString());
      setCurrentAssessment(response);
      setAssessmentHistory(prev => ({
        ...prev,
        [selectedPatient.subject_id]: response
      }));
    } catch (error) {
      const errorMessage = formatErrorMessage(error);
      setAssessmentError(errorMessage);
      
      // Log error for debugging
      console.error('Assessment failed:', error);
    } finally {
      setAssessmentLoading(false);
    }
  };

  const clearAssessment = () => {
    setCurrentAssessment(null);
    setAssessmentError(null);
  };

  // Track when telemetry was last received
  const currentVitalsForEffect = vitals[effectiveSelectedId ?? 0];
  const latestVitalTimestamp = currentVitalsForEffect?.length > 0
    ? currentVitalsForEffect[currentVitalsForEffect.length - 1].charttime // watch actual data instead of array length
    : null;

  useEffect(() => {
    if (latestVitalTimestamp) {
      setLastTelemetryAt(new Date());
    }
  }, [latestVitalTimestamp]);

  // Tick seconds-ago counter every second
  useEffect(() => {
    const ticker = setInterval(() => {
      if (lastTelemetryAt) {
        setSyncSecondsAgo(Math.floor((Date.now() - lastTelemetryAt.getTime()) / 1000));
      }
    }, 1000);
    return () => clearInterval(ticker);
  }, [lastTelemetryAt]);

  if (isLoadingDemographics || !mounted) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center bg-white dark:bg-slate-950 gap-4 transition-colors duration-500">
        <Activity className="text-blue-600 animate-pulse" size={48} />
        <span className="text-xs font-black text-slate-400 uppercase tracking-[0.4em] animate-pulse">Establishing Secure Stream</span>
      </div>
    );
  }

  if (!selectedPatient) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center bg-white dark:bg-slate-950 gap-4">
        <Activity className="text-slate-300" size={48} />
        <p className="text-sm font-black text-slate-400 uppercase tracking-widest">No Patients in Your Department</p>
        {currentUser?.specialty && <p className="text-xs text-slate-400">({SPECIALTY_LABELS[currentUser.specialty]})</p>}
        <button onClick={handleLogout} className="mt-4 px-6 py-2 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-black text-xs uppercase tracking-widest">Logout</button>
      </div>
    );
  }

  // ── Live vital derivations — all update as ingestor pushes every 10s ──
  const latest = (itemids: number[]) => {
    const matches = currentVitals.filter(v => itemids.includes(v.itemid));
    return matches[matches.length - 1];
  };

  const hrRecord   = latest([211, 220045]);
  const mapRecord  = latest([456, 52, 6702, 443, 220052, 220181, 225312]);
  const spo2Record = latest([646, 220277]);
  const rrRecord   = latest([615, 618, 220210, 224690]);
  const tempRecord = latest([223761, 678]);   // °C or °F

  const liveHR   = hrRecord?.valuenum   ?? selectedPatient.bpm;
  const liveMAP  = mapRecord?.valuenum  ?? null;
  const liveSPO2 = spo2Record?.valuenum ?? null;
  const liveRR   = rrRecord?.valuenum   ?? null;
  const liveTemp = tempRecord?.valuenum ?? null;

  // Outlier from ANY live vital = alert
  const anyOutlier = [hrRecord, mapRecord, spo2Record, rrRecord, tempRecord]
    .some(r => r?.is_outlier);
  const isAlert = selectedPatient.is_alert || anyOutlier
    || (liveHR > 130) || (liveMAP !== null && liveMAP < 65)
    || (liveSPO2 !== null && liveSPO2 < 92);

  const sepsisProbability = currentAssessment ? currentAssessment.risk_score 
    : isAlert ? 84
    : selectedPatient?.diagnosis?.toUpperCase().includes("SEPSIS") ? 42 : 12;
    
  const status = currentAssessment 
    ? (currentAssessment.risk_level.toLowerCase() as "stable" | "moderate" | "critical")
    : isAlert ? "critical" 
    : (sepsisProbability > 15 ? "moderate" : "stable");
    
  const bedUnit = `ICU-${String(selectedPatient.subject_id % 6 + 1).padStart(2, "0")}${String.fromCharCode(65 + (selectedPatient.subject_id % 4))}`;

  // ── Dynamic protocol status — escalates based on live vital readings ──
  const liveStatus = (
    base: string,
    escalateIf: boolean,
    deescalateIf?: boolean
  ): string => {
    if (escalateIf) return "Critical";
    if (deescalateIf) return "Stable";
    return base;
  };

  const getProtocols = (diagnosis: string = "") => {
    const d = diagnosis.toUpperCase();
    const hrHigh  = liveHR  !== null && liveHR  > 120;
    const mapLow  = liveMAP !== null && liveMAP < 65;
    const spo2Low = liveSPO2 !== null && liveSPO2 < 92;
    const rrHigh  = liveRR  !== null && liveRR  > 24;

    if (d.includes("SEPSIS") || d.includes("SEPTIC")) return [
      { title: "Fluid Resuscitation", desc: "30 ml/kg crystalloid bolus in first 3 hrs. Reassess at 6 hrs.", status: liveStatus("Critical", mapLow) },
      { title: "Broad-Spectrum Antibiotics", desc: "Vancomycin + Piperacillin/Tazobactam Q8H. Culture-guided de-escalation.", status: "Active" },
      { title: "Source Control", desc: "Surgical/radiology consult for drainage or debridement.", status: "Active" },
      { title: "Vasopressors (PRN)", desc: "Norepinephrine target MAP ≥ 65 mmHg. Escalate as needed.", status: liveStatus("Pending", mapLow) },
    ];
    if (d.includes("PNEUMONIA")) return [
      { title: "Oxygen Therapy", desc: "Target SpO₂ 92–96% via nasal cannula. Consider HFNC if refractory.", status: liveStatus("Active", spo2Low) },
      { title: "Antibiotic Coverage", desc: "Azithromycin + Beta-lactam (community); Vanc + Cefepime (HAP).", status: "Active" },
      { title: "Sputum & Blood Cultures", desc: "Awaiting final sensitivity — repeat if no improvement at 48h.", status: "Pending" },
      { title: "Early Mobilization", desc: "Breathing exercises Q4H. Incentive spirometry TID.", status: liveStatus("Stable", false, !spo2Low) },
    ];
    if (d.includes("ARREST") || d.includes("CARDIAC") || d.includes("HEART FAILURE")) return [
      { title: "Cardiac Monitoring", desc: "Continuous 12-lead ECG. Troponin Q6H × 3.", status: liveStatus("Critical", hrHigh) },
      { title: "Diuresis", desc: "IV Lasix 40 mg STAT. Target negative fluid balance 1–2 L/24h.", status: liveStatus("Active", mapLow) },
      { title: "Cardiology Consult", desc: "Urgent echocardiogram ordered. Hemodynamic optimization.", status: "Active" },
      { title: "Anticoagulation", desc: "Heparin infusion per weight-based protocol. PTT Q6H.", status: "Pending" },
    ];
    if (d.includes("STROKE") || d.includes("CVA") || d.includes("CEREBROVASCULAR")) return [
      { title: "Neurological Monitoring", desc: "NIHSS score Q2H. Pupil checks Q1H.", status: "Critical" },
      { title: "tPA / Thrombectomy", desc: "Within 4.5h window — neurology activating stroke protocol.", status: "Active" },
      { title: "BP Management", desc: "Target < 185/110 mmHg pre-tPA. Labetalol/Nicardipine PRN.", status: liveStatus("Active", mapLow) },
      { title: "Stroke Workup", desc: "CT Angiography & Diffusion MRI ordered. Embolic source screen.", status: "Pending" },
    ];
    if (d.includes("RENAL") || d.includes("KIDNEY") || d.includes("AKI") || d.includes("FAILURE")) return [
      { title: "Fluid Balance", desc: "Strict I/O monitoring. Restrict IV fluids if fluid-overloaded.", status: liveStatus("Active", mapLow) },
      { title: "Nephrotoxin Avoidance", desc: "Hold NSAIDs, aminoglycosides, IV contrast. Review all meds.", status: "Active" },
      { title: "Dialysis Assessment", desc: "Nephrology consult placed. CRRT initiation criteria under review.", status: liveStatus("Pending", mapLow && rrHigh) },
      { title: "Electrolyte Correction", desc: "Treat hyperkalemia per protocol. Kayexalate PRN.", status: liveStatus("Stable", hrHigh) },
    ];
    if (d.includes("COPD") || d.includes("RESPIRATORY") || d.includes("HYPOXIA")) return [
      { title: "Bronchodilators", desc: "Albuterol + Ipratropium Q4H nebulizers. Titrate to response.", status: liveStatus("Active", rrHigh) },
      { title: "NIV / BiPAP", desc: "Non-invasive ventilation initiated. IPAP 14 / EPAP 5.", status: liveStatus("Active", spo2Low) },
      { title: "Systemic Steroids", desc: "Methylprednisolone 125 mg IV Q8H × 3 days.", status: "Stable" },
      { title: "Intubation Readiness", desc: "Respiratory threshold met — anesthesia on standby.", status: liveStatus("Pending", spo2Low && rrHigh) },
    ];
    return [
      { title: "Vital Sign Monitoring", desc: "Q2H documentation. Continuous pulse oximetry.", status: liveStatus("Active", isAlert) },
      { title: "DVT Prophylaxis", desc: "Enoxaparin 40 mg SQ daily. Sequential compression device active.", status: "Active" },
      { title: "Fall & Pressure Injury Prevention", desc: "Hourly repositioning. Foam mattress overlay applied.", status: "Active" },
      { title: "Nutrition Assessment", desc: "Dietitian consult placed. Enteral nutrition goal 25 kcal/kg/day.", status: "Pending" },
    ];
  };
  const protocols = getProtocols(selectedPatient?.diagnosis);

  // Dynamic Assessment Block Configuration based on AI Analysis
  const getDynamicAssessment = () => {
    // Check if we have AI analysis results from the AI Analysis Panel
    // This would be set when AI analysis is run
    const aiResults = typeof window !== 'undefined' ? 
      JSON.parse(window.localStorage.getItem('latest-ai-analysis') || 'null') : null;
    
    // If AI analysis is available, use it to determine risk assessment
    if (aiResults && aiResults.overall_risk_score !== undefined) {
      const riskScore = aiResults.overall_risk_score;
      const sepsisRisk = aiResults.sepsis_risk?.probability || 0;
      const confidence = Math.round((aiResults.confidence_score || 0) * 100);
      
      if (riskScore >= 80 || sepsisRisk >= 75) {
        return {
          bgClass: "bg-gradient-to-r from-red-600/20 to-red-700/20 border-red-500",
          iconClass: "text-red-600",
          titleClass: "text-red-900 dark:text-red-100",
          subtitleClass: "text-red-700 dark:text-red-300",
          scoreClass: "text-red-600 dark:text-red-400", 
          levelClass: "text-red-800 dark:text-red-200",
          title: "SEPSIS RISK DETECTED",
          subtitle: "Clinical markers suggest immediate hemodynamic intervention. Elevated lactate and HR detected.",
          riskScore: riskScore,
          riskLevel: "CRITICAL",
          confidence: `${confidence}%`,
          icon: "⚠️",
          liveIndicator: "🔴 LIVE AI ANALYSIS"
        };
      } else if (riskScore >= 60 || sepsisRisk >= 50) {
        return {
          bgClass: "bg-gradient-to-r from-orange-500/20 to-orange-600/20 border-orange-400",
          iconClass: "text-orange-600",
          titleClass: "text-orange-900 dark:text-orange-100",
          subtitleClass: "text-orange-700 dark:text-orange-300",
          scoreClass: "text-orange-600 dark:text-orange-400",
          levelClass: "text-orange-800 dark:text-orange-200",
          title: "DETERIORATING PATTERNS",
          subtitle: "Multiple concerning trends detected requiring close monitoring and intervention.",
          riskScore: riskScore,
          riskLevel: "HIGH RISK",
          confidence: `${confidence}%`,
          icon: "⚠️",
          liveIndicator: "🟡 LIVE AI ANALYSIS"
        };
      } else if (riskScore >= 35) {
        return {
          bgClass: "bg-gradient-to-r from-yellow-400/20 to-yellow-500/20 border-yellow-400",
          iconClass: "text-yellow-600",
          titleClass: "text-yellow-900 dark:text-yellow-100",
          subtitleClass: "text-yellow-700 dark:text-yellow-300",
          scoreClass: "text-yellow-600 dark:text-yellow-400",
          levelClass: "text-yellow-800 dark:text-yellow-200",
          title: "CONCERNING TRENDS",
          subtitle: "Mixed clinical patterns observed. Some vital signs showing concerning trends.",
          riskScore: riskScore,
          riskLevel: "MODERATE",
          confidence: `${confidence}%`,
          icon: "⚠️",
          liveIndicator: "🟡 LIVE AI ANALYSIS"
        };
      } else {
        return {
          bgClass: "bg-gradient-to-r from-green-500/20 to-green-600/20 border-green-400",
          iconClass: "text-green-600",
          titleClass: "text-green-900 dark:text-green-100",
          subtitleClass: "text-green-700 dark:text-green-300",
          scoreClass: "text-green-600 dark:text-green-400",
          levelClass: "text-green-800 dark:text-green-200",
          title: "STABLE: LOW RISK",
          subtitle: "All clinical markers within normal thresholds. Patient currently showing signs of recovery.",
          riskScore: riskScore,
          riskLevel: "LOW RISK",
          confidence: `${confidence}%`,
          icon: "✅",
          liveIndicator: "🟢 LIVE AI ANALYSIS"
        };
      }
    }
    
    // Fallback to current assessment or default values when AI is off
    if (currentAssessment) {
      return {
        bgClass: "bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800/50",
        iconClass: "text-blue-600 dark:text-blue-400",
        titleClass: "text-blue-900 dark:text-blue-100",
        subtitleClass: "text-blue-700 dark:text-blue-300",
        scoreClass: "text-blue-600 dark:text-blue-400",
        levelClass: "text-blue-800 dark:text-blue-200",
        title: "AI ASSESSMENT COMPLETE",
        subtitle: currentAssessment?.clinical_summary || "Assessment analysis completed successfully.",
        riskScore: currentAssessment?.risk_score || 0,
        riskLevel: currentAssessment?.risk_level || "UNKNOWN",
        confidence: "85%",
        icon: "🧠",
        liveIndicator: "AI STATIC ANALYSIS"
      };
    }
    
    // Default state when no assessment available
    return {
      bgClass: "bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800/20 dark:to-slate-900/20 border-slate-200 dark:border-slate-700/50",
      iconClass: "text-slate-600 dark:text-slate-400",
      titleClass: "text-slate-900 dark:text-slate-100",
      subtitleClass: "text-slate-700 dark:text-slate-300",
      scoreClass: "text-slate-600 dark:text-slate-400",
      levelClass: "text-slate-800 dark:text-slate-200",
      title: "PRIMARY RISK ASSESSMENT",
      subtitle: "Awaiting AI analysis for risk assessment.",
      riskScore: 0,
      riskLevel: "PENDING",
      confidence: "--",
      icon: "🔄",
      liveIndicator: "AWAITING ANALYSIS"
    };
  };

  const dynamicAssessment = getDynamicAssessment();


  return (
    <main className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden antialiased text-slate-900 dark:text-slate-100 transition-colors duration-500">
      <PatientSidebar
        patients={visiblePatients.map(p => ({
          subject_id: p.subject_id,
          gender: p.gender,
          diagnosis: p.diagnosis,
          bpm: vitals[p.subject_id]?.slice(-1)[0]?.valuenum || p.bpm || 0,
          is_alert: p.is_alert || vitals[p.subject_id]?.slice(-1)[0]?.is_outlier || (vitals[p.subject_id]?.slice(-1)[0]?.valuenum > 130)
        }))}
        selectedId={effectiveSelectedId!}
        onSelect={setSelectedId}
      />

      <div className="flex-1 overflow-y-auto px-12 py-10 space-y-8 custom-scrollbar">

        {/* ── Header ── */}
        <motion.div key={selectedPatient.subject_id} initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">

          {/* Left: title + patient meta */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-xl shadow-blue-500/20">
                <Zap size={24} fill="currentColor" />
              </div>
              <div>
                <h2 className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] leading-none mb-1.5 flex items-center gap-2">
                  Intensive Care Unit
                  {currentUser?.role === "admin" && (
                    <span className="bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400 px-2 py-0.5 rounded text-[8px] uppercase tracking-widest">Admin</span>
                  )}
                  {currentUser?.role === "doctor" && currentUser.specialty && (
                    <span className="bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400 px-2 py-0.5 rounded text-[8px] uppercase tracking-widest">
                      {SPECIALTY_LABELS[currentUser.specialty]}
                    </span>
                  )}
                </h2>
                <h1 className="text-2xl font-black tracking-tight">PATIENT <span className="text-blue-600">MONITOR</span></h1>
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
                <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Bed</p>
                <p className="text-sm font-black text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <Bed size={14} className="text-blue-600" /> {bedUnit}
                </p>
              </div>
              <div>
                <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Status</p>
                <p className={cn("text-sm font-black uppercase", isAlert ? "text-rose-600" : "text-emerald-600")}>{isAlert ? "CRITICAL" : "STABLE"}</p>
              </div>
            </div>
          </div>

          {/* ── Right: all 4 controls together ── */}
          <div className="flex items-center gap-2">
            {/* 1. Analytics (admin only) */}
            {currentUser?.role === "admin" && (
              <Link href="/admin"
                className="relative flex items-center gap-1.5 px-3 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-xs font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 shadow-sm transition-colors">
                <BarChart2 size={14} /> Analytics
                {pendingCount > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-amber-500 text-white text-[8px] font-black rounded-full flex items-center justify-center">{pendingCount}</span>
                )}
              </Link>
            )}

            {/* 2. AI Assessment */}
            <button 
              onClick={assessmentLoading ? undefined : runAssessment}
              disabled={assessmentLoading || !selectedPatient}
              title={assessmentLoading ? "Running AI Assessment..." : "Run AI Assessment"}
              className={cn(
                "relative flex items-center gap-1.5 px-3 py-2.5 rounded-2xl text-xs font-black uppercase tracking-widest shadow-sm transition-all duration-200",
                assessmentLoading 
                  ? "bg-blue-600/10 border-blue-600/20 text-blue-600 cursor-not-allowed" 
                  : currentAssessment
                  ? "bg-emerald-600/10 border-emerald-600/20 text-emerald-600 hover:bg-emerald-600/20"
                  : "bg-blue-600 border-blue-600 text-white hover:bg-blue-700",
                "border"
              )}
            >
              {assessmentLoading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Analyzing...
                </>
              ) : currentAssessment ? (
                <>
                  <Brain size={14} />
                  Risk: {currentAssessment.risk_score}
                </>
              ) : (
                <>
                  <Brain size={14} />
                  AI Assess
                </>
              )}
              {currentAssessment && !assessmentLoading && (
                <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-emerald-500 text-white text-[8px] font-black rounded-full flex items-center justify-center">✓</span>
              )}
            </button>

            {/* 3. Shift Handover Report */}
            <button 
              onClick={() => setShowHandoverReport(true)}
              disabled={!selectedPatient}
              title="Generate Shift Handover Report"
              className={cn(
                "flex items-center gap-1.5 px-3 py-2.5 rounded-2xl text-xs font-black uppercase tracking-widest shadow-sm transition-all duration-200 border",
                selectedPatient
                  ? "bg-purple-600 border-purple-600 text-white hover:bg-purple-700"
                  : "bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed"
              )}
            >
              <FileText size={14} />
              Handover
            </button>

            {/* 4. Live Feed */}
            <div className="flex items-center gap-1.5 px-3 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Live Feed</span>
            </div>

            {/* 5. Theme toggle */}
            <button onClick={toggleTheme} title={theme === "dark" ? "Light Mode" : "Dark Mode"}
              className="w-10 h-10 flex items-center justify-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
              {theme === "dark" ? <Sun size={15} className="text-amber-500" /> : <SunMoon size={15} className="text-blue-600" />}
            </button>

            {/* 5. Logout */}
            <button onClick={handleLogout} title="Logout"
              className="w-10 h-10 flex items-center justify-center bg-slate-900 dark:bg-white rounded-2xl shadow-sm text-white dark:text-slate-900 hover:opacity-80 transition-opacity">
              <LogOut size={15} />
            </button>
          </div>
        </motion.div>

        {/* Sepsis Banner */}
        <motion.section key={`banner-${selectedPatient.subject_id}`} initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }} className="w-full">
          <SepsisBanner probability={sepsisProbability} status={status} lastCheck={new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })} />
        </motion.section>

        {/* Assessment Results Panel */}
        <AnimatePresence mode="wait">
          {assessmentError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="w-full"
            >
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 rounded-3xl p-6 flex items-center gap-4">
                <AlertTriangle className="text-red-600 dark:text-red-400" size={24} />
                <div>
                  <h3 className="font-bold text-red-900 dark:text-red-100 mb-1">Assessment Failed</h3>
                  <p className="text-sm text-red-700 dark:text-red-300">{assessmentError}</p>
                  {isNetworkError(new Error(assessmentError)) && (
                    <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                      Make sure the backend server is running on http://localhost:8000
                    </p>
                  )}
                  <button
                    onClick={clearAssessment}
                    className="text-xs font-bold text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 mt-2 underline"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </motion.div>
          )}
          
        </AnimatePresence>

        {/* Tab Navigation */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-1 bg-white dark:bg-slate-900 rounded-2xl p-2 border border-slate-200 dark:border-slate-800 shadow-sm"
        >
          <button
            onClick={() => setActiveTab("monitoring")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all duration-200",
              activeTab === "monitoring"
                ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
            )}
          >
            <Activity size={16} />
            Clinical Monitoring
          </button>
          
          <button
            onClick={() => setActiveTab("ai")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all duration-200",
              activeTab === "ai"
                ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg shadow-purple-500/20"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
            )}
          >
            <Brain size={16} />
            🤖 AI Analysis Pipeline
          </button>
          
          <button
            onClick={() => setActiveTab("family")}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all duration-200",
              activeTab === "family"
                ? "bg-green-600 text-white shadow-lg shadow-green-500/20"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
            )}
          >
            <Heart size={16} />
            Family Communication
          </button>
        </motion.div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {activeTab === "monitoring" && (
            <motion.div
              key="monitoring-tab"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="space-y-8"
            >

        {/* ── Live Vitals Strip — all values from injected telemetry ── */}
        <motion.div
          key={`vitals-strip-${selectedPatient.subject_id}`}
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
          className="grid grid-cols-2 md:grid-cols-5 gap-4"
        >
          {[
            {
              label: "Heart Rate", unit: "BPM", icon: "💓",
              value: liveHR, record: hrRecord,
              normal: (v: number) => v >= 60 && v <= 100,
              color: "blue",
            },
            {
              label: "MAP", unit: "mmHg", icon: "🩸",
              value: liveMAP, record: mapRecord,
              normal: (v: number) => v >= 70 && v <= 100,
              color: "cyan",
            },
            {
              label: "SpO₂", unit: "%", icon: "🫁",
              value: liveSPO2, record: spo2Record,
              normal: (v: number) => v >= 95,
              color: "emerald",
            },
            {
              label: "Resp Rate", unit: "/min", icon: "🌬️",
              value: liveRR, record: rrRecord,
              normal: (v: number) => v >= 12 && v <= 20,
              color: "violet",
            },
            {
              label: "Temperature", unit: tempRecord?.valueuom === "degF" ? "°F" : "°C", icon: "🌡️",
              value: liveTemp, record: tempRecord,
              normal: (v: number) => tempRecord?.valueuom === "degF" ? (v >= 97 && v <= 99.5) : (v >= 36.1 && v <= 37.2),
              color: "rose",
            },
          ].map((vital, i) => {
            const isCritical = vital.record?.is_outlier || (vital.value !== null && !vital.normal(vital.value!));
            const hasData = vital.value !== null && vital.value !== undefined;
            return (
              <motion.div
                key={vital.label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 + i * 0.05 }}
                className={cn(
                  "relative p-5 rounded-3xl border transition-all duration-700",
                  isCritical
                    ? "bg-rose-50 dark:bg-rose-900/20 border-rose-200 dark:border-rose-800 shadow-rose-500/10 shadow-lg"
                    : "bg-white dark:bg-slate-900 border-slate-100 dark:border-slate-800 shadow-sm"
                )}
              >
                {isCritical && (
                  <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                )}
                <div className="text-lg mb-1">{vital.icon}</div>
                <div className={cn(
                  "text-2xl font-black tracking-tighter leading-none",
                  isCritical ? "text-rose-600 dark:text-rose-400" : "text-slate-900 dark:text-slate-100"
                )}>
                  {hasData ? vital.value!.toFixed(1) : "—"}
                  <span className="text-xs font-black text-slate-400 ml-1">{vital.unit}</span>
                </div>
                <div className="text-[9px] font-black text-slate-400 uppercase tracking-[0.15em] mt-1.5">
                  {vital.label}
                </div>
                {hasData && (
                  <div className={cn(
                    "text-[8px] font-black uppercase mt-1",
                    isCritical ? "text-rose-500" : "text-emerald-500"
                  )}>
                    {isCritical ? "⚠ OUT OF RANGE" : "✓ NORMAL"}
                  </div>
                )}
              </motion.div>
            );
          })}
        </motion.div>

        {/* Vitals Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <VitalTrend label="Heart Rate Telemetry" unit="BPM" color="#2563EB" data={currentVitals.filter(v => [211, 220045].includes(v.itemid))} yMin={30} yMax={200} className="shadow-xl shadow-blue-500/5" />
          <VitalTrend label="MAP Trends" unit="mmHg" color="#0891B2" data={currentVitals.filter(v => [456, 52, 6702, 443, 220052, 220181, 225312].includes(v.itemid))} yMin={40} yMax={140} />
        </div>

        {/* Clinical Profile + Protocols */}
        <motion.section key={`profile-${selectedPatient.subject_id}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-100 dark:border-slate-800 shadow-2xl shadow-slate-200/20 dark:shadow-black/40 overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-3 divide-x divide-slate-100 dark:divide-slate-800">
            <div className="p-10 bg-slate-50/50 dark:bg-slate-900/50">
              <div className="flex items-center gap-3 mb-8">
                <div className="w-8 h-8 rounded-lg bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 flex items-center justify-center">
                  <Database size={16} />
                </div>
                <h3 className="text-sm font-black text-slate-800 dark:text-slate-100 uppercase tracking-tight">Clinical Profile</h3>
              </div>
              <div className="space-y-6">
                {[
                  { label: "Admission Type", val: selectedPatient.admission_type || "N/A", icon: <Activity size={14} className="text-blue-600" /> },
                  { label: "Insurance Tier",  val: selectedPatient.insurance || "N/A",     icon: <Thermometer size={14} className="text-rose-500" /> },
                  { label: "Language",        val: selectedPatient.language || "EN-US",    icon: <Wind size={14} className="text-emerald-500" /> },
                ].map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <div className="flex items-center gap-2">{item.icon}<span className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">{item.label}</span></div>
                    <span className="text-sm font-black text-slate-800 dark:text-slate-200 font-mono uppercase tracking-tighter">{item.val}</span>
                  </div>
                ))}
              </div>
              <div className={cn("mt-10 p-6 rounded-3xl text-white shadow-xl ring-4", isAlert ? "bg-rose-600 shadow-rose-500/20 ring-rose-600/10" : "bg-blue-600 shadow-blue-500/20 ring-blue-600/10")}>
                <div className="text-[10px] font-black uppercase tracking-[0.2em] opacity-80 mb-2">Primary Diagnosis</div>
                <div className="text-lg font-black tracking-tight leading-tight uppercase">{selectedPatient.diagnosis || "CLINICAL EVALUATION"}</div>
              </div>
            </div>

            <div className="lg:col-span-2 p-10 relative">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3 text-slate-800 dark:text-slate-100">
                  <ClipboardList size={20} className="text-blue-600" />
                  <h3 className="text-sm font-black uppercase tracking-tight">Active Clinical Protocols</h3>
                </div>
                <div className={cn(
                  "flex items-center gap-1.5 px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all duration-500",
                  isAlert
                    ? "bg-rose-50 dark:bg-rose-900/50 text-rose-600"
                    : "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400"
                )}>
                  <span className={cn(
                    "w-1.5 h-1.5 rounded-full",
                    isAlert ? "bg-rose-500 animate-ping" : "bg-emerald-500 animate-pulse"
                  )} />
                  {isAlert
                    ? "⚠ Urgent"
                    : syncSecondsAgo === null
                      ? "Connecting..."
                      : syncSecondsAgo < 15
                        ? `Live · ${syncSecondsAgo}s ago`
                        : `Last sync ${syncSecondsAgo}s ago`
                  }
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {protocols.map((protocol, idx) => (
                  <div key={idx} className="p-6 rounded-[2rem] border border-slate-100 dark:border-slate-800 hover:border-blue-200 dark:hover:border-blue-900 hover:bg-blue-50/20 dark:hover:bg-blue-900/20 transition-all group">
                    <div className="flex justify-between items-center mb-1.5">
                      <h4 className="text-xs font-black text-slate-800 dark:text-slate-100 uppercase">{protocol.title}</h4>
                      <span className={cn("text-[8px] font-black uppercase tracking-widest px-2.5 py-1 rounded-lg",
                        protocol.status === "Critical" ? "bg-rose-100 text-rose-600 animate-pulse" :
                        protocol.status === "Pending"  ? "bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400" :
                        "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400")}>{protocol.status}</span>
                    </div>
                    <p className="text-[10px] font-bold text-slate-400 dark:text-slate-500 group-hover:text-slate-500 dark:group-hover:text-slate-400 leading-relaxed uppercase tracking-wider">{protocol.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.section>
        
            </motion.div>
          )}
          
          {activeTab === "ai" && (
            <motion.div
              key="ai-tab"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <AIAnalysisPanel 
                patientId={selectedPatient.subject_id}
                className="space-y-6"
              />
            </motion.div>
          )}
          
          {activeTab === "family" && (
            <motion.div
              key="family-tab"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <FamilyCommunicationPanel 
                patientId={selectedPatient.subject_id}
                className="space-y-6"
              />
            </motion.div>
          )}
        </AnimatePresence>
        
      </div>

      {/* Shift Handover Report Modal */}
      <AnimatePresence>
        {showHandoverReport && selectedPatient && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowHandoverReport(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden"
              onClick={e => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-slate-200">
                <h2 className="text-xl font-bold text-slate-900">
                  Shift Handover Report - {selectedPatient.subject_id}
                </h2>
                <button
                  onClick={() => setShowHandoverReport(false)}
                  className="w-10 h-10 flex items-center justify-center bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Modal Content */}
              <div className="overflow-y-auto max-h-[calc(90vh-120px)]">
                <div className="p-6">
                  <ShiftHandoverReport
                    patient={selectedPatient}
                    vitals={currentVitals}
                    onPrintReport={() => window.print()}
                  />
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
