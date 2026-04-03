"use client";
import React, { useState, useMemo } from "react";
import { User, ShieldCheck, ShieldAlert, PanelLeftClose, PanelLeftOpen, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

type FilterType = "all" | "critical" | "sepsis" | "pneumonia" | "cardiac" | "renal" | "stroke" | "respiratory";

interface FilterOption {
  key: FilterType;
  label: string;
  color: string;
}

const CONDITION_FILTERS: FilterOption[] = [
  { key: "all", label: "All", color: "" },
  { key: "critical", label: "Critical", color: "rose" },
  { key: "sepsis", label: "Sepsis", color: "orange" },
  { key: "pneumonia", label: "Pneumo", color: "sky" },
  { key: "cardiac", label: "Cardiac", color: "pink" },
  { key: "renal", label: "Renal", color: "violet" },
  { key: "stroke", label: "Stroke", color: "yellow" },
  { key: "respiratory", label: "Resp", color: "teal" },
];

interface Patient {
  subject_id: number;
  gender: string;
  diagnosis?: string;
  bpm: number;
  is_alert: boolean;
}

interface PatientSidebarProps {
  patients: Patient[];
  selectedId: number;
  onSelect: (id: number) => void;
}

function matchesConditionFilter(filter: FilterType, patient: Patient): boolean {
  if (filter === "all") return true;
  if (filter === "critical") return patient.is_alert;
  const d = (patient.diagnosis || "").toUpperCase();
  if (filter === "sepsis") return d.includes("SEPSIS") || d.includes("SEPTIC");
  if (filter === "pneumonia") return d.includes("PNEUMONIA");
  if (filter === "cardiac") return d.includes("CARDIAC") || d.includes("ARREST") || d.includes("HEART FAILURE") || d.includes("MI") || d.includes("CORONARY");
  if (filter === "renal") return d.includes("RENAL") || d.includes("KIDNEY") || d.includes("AKI") || d.includes("FAILURE");
  if (filter === "stroke") return d.includes("STROKE") || d.includes("CVA") || d.includes("CEREBROVASCULAR");
  if (filter === "respiratory") return d.includes("COPD") || d.includes("RESPIRATORY") || d.includes("HYPOXIA") || d.includes("ASTHMA");
  return true;
}

export function PatientSidebar({ patients, selectedId, onSelect }: PatientSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<FilterType>("all");

  const filteredPatients = useMemo(() => {
    return patients.filter((p) => {
      const matchesSearch = 
        p.subject_id.toString().includes(searchQuery.toLowerCase()) ||
        (p.diagnosis?.toLowerCase() || "").includes(searchQuery.toLowerCase());
      
      const matchesFilter = matchesConditionFilter(filterType, p);
      
      return matchesSearch && matchesFilter;
    });
  }, [patients, searchQuery, filterType]);

  const getFilterStyle = (filter: FilterOption, isActive: boolean) => {
    if (filter.key === "all") {
      return isActive
        ? "bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 border-transparent shadow-md"
        : "bg-white dark:bg-slate-900 text-slate-500 border-slate-200 dark:border-slate-800 hover:border-slate-300";
    }
    const colorMap: Record<string, string> = {
      rose: isActive ? "bg-rose-600 text-white border-transparent shadow-lg shadow-rose-200/20" : "bg-white dark:bg-slate-900 text-slate-500 border-slate-200 dark:border-slate-800 hover:border-rose-200",
      orange: isActive ? "bg-orange-500 text-white border-transparent shadow-lg shadow-orange-200/20" : "bg-white dark:bg-slate-900 text-slate-500 border-slate-200 dark:border-slate-800 hover:border-orange-200",
      sky: isActive ? "bg-sky-500 text-white border-transparent shadow-lg shadow-sky-200/20" : "bg-white dark:bg-slate-900 text-slate-500 border-slate-200 dark:border-slate-800 hover:border-sky-200",
      pink: isActive ? "bg-pink-500 text-white border-transparent shadow-lg shadow-pink-200/20" : "bg-white dark:bg-slate-900 text-slate-500 border-slate-200 dark:border-slate-800 hover:border-pink-200",
      violet: isActive ? "bg-violet-600 text-white border-transparent shadow-lg shadow-violet-200/20" : "bg-white dark:bg-slate-900 text-slate-500 border-slate-200 dark:border-slate-800 hover:border-violet-200",
      yellow: isActive ? "bg-yellow-500 text-white border-transparent shadow-lg shadow-yellow-200/20" : "bg-white dark:bg-slate-900 text-slate-500 border-slate-200 dark:border-slate-800 hover:border-yellow-200",
      teal: isActive ? "bg-teal-500 text-white border-transparent shadow-lg shadow-teal-200/20" : "bg-white dark:bg-slate-900 text-slate-500 border-slate-200 dark:border-slate-800 hover:border-teal-200",
    };
    return colorMap[filter.color] || colorMap.rose;
  };

  const getDotColor = (filterKey: FilterType, isActive: boolean): string => {
    if (filterKey === "all") return "";
    const dotMap: Record<string, string> = {
      critical: isActive ? "bg-white animate-pulse" : "bg-rose-500",
      sepsis: isActive ? "bg-white animate-pulse" : "bg-orange-400",
      pneumonia: isActive ? "bg-white animate-pulse" : "bg-sky-400",
      cardiac: isActive ? "bg-white animate-pulse" : "bg-pink-400",
      renal: isActive ? "bg-white animate-pulse" : "bg-violet-400",
      stroke: isActive ? "bg-white animate-pulse" : "bg-yellow-400",
      respiratory: isActive ? "bg-white animate-pulse" : "bg-teal-400",
    };
    return dotMap[filterKey] || "bg-rose-500";
  };

  return (
    <aside
      className={cn(
        "h-screen bg-[#F1F5F9]/30 dark:bg-slate-950/80 backdrop-blur-xl border-r border-slate-200/60 dark:border-slate-800/60 flex flex-col gap-4 overflow-hidden transition-[width] duration-300 ease-in-out z-50",
        isCollapsed ? "w-24" : "w-80"
      )}
    >
      {/* Header */}
      <div className={cn("p-6 pb-2 flex items-start", isCollapsed ? "justify-center" : "justify-between")}>
        {!isCollapsed && (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
              <h2 className="text-xl font-black text-slate-900 dark:text-slate-100 tracking-tight leading-none uppercase">Clinical Registry</h2>
            </div>
            <p className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest px-4">Active Patients</p>
          </motion.div>
        )}

        <button
          type="button"
          onClick={() => setIsCollapsed((s) => !s)}
          className="shrink-0 w-10 h-10 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-all flex items-center justify-center shadow-sm"
          aria-label={isCollapsed ? "Expand" : "Collapse"}
        >
          {isCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </button>
      </div>

      {/* Search and Filters */}
      {!isCollapsed && (
        <div className="px-4 space-y-3">
          {/* Search */}
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={14} />
            <input
              type="text"
              placeholder="Search ID or Diagnosis..."
              value={searchQuery}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-xs font-bold text-slate-700 dark:text-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/50 transition-all outline-none"
            />
          </div>

          {/* Quick Condition Filters - 2 rows */}
          <div className="grid grid-cols-4 gap-1.5">
            {CONDITION_FILTERS.map((filter) => {
              const isActive = filterType === filter.key;
              return (
                <button
                  key={filter.key}
                  onClick={() => setFilterType(filter.key)}
                  className={cn(
                    "py-1.5 px-1 rounded-xl text-[9px] font-black uppercase tracking-wide border transition-all flex items-center justify-center gap-1",
                    getFilterStyle(filter, isActive)
                  )}
                >
                  {filter.key !== "all" && (
                    <div className={cn("w-1.5 h-1.5 rounded-full shrink-0", getDotColor(filter.key, isActive))} />
                  )}
                  {filter.label}
                </button>
              );
            })}
          </div>

          {/* Patient count */}
          <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest text-center">
            {filteredPatients.length} of {patients.length} patients
          </p>
        </div>
      )}

      {/* Patient List */}
      <div className={cn("flex-1 overflow-y-auto pb-6 space-y-3 custom-scrollbar", isCollapsed ? "px-4" : "px-4")}>
        <AnimatePresence mode="popLayout">
          {filteredPatients.map((patient, idx) => (
            <motion.button
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ delay: idx * 0.02 }}
              key={patient.subject_id}
              onClick={() => onSelect(patient.subject_id)}
              className={cn(
                "w-full rounded-3xl transition-all duration-300 relative group border",
                isCollapsed ? "p-3 flex items-center justify-center" : "p-4 text-left",
                selectedId === patient.subject_id
                  ? "bg-white dark:bg-slate-900 shadow-xl shadow-blue-500/10 border-blue-200 dark:border-blue-800 ring-1 ring-blue-500/10"
                  : "bg-white/50 dark:bg-slate-900/40 border-slate-100 dark:border-slate-800/50 hover:bg-white dark:hover:bg-slate-900 hover:border-slate-200 hover:shadow-md",
                patient.is_alert && "border-rose-400 dark:border-rose-900 shadow-lg shadow-rose-500/15"
              )}
            >
              {isCollapsed ? (
                <div className="relative">
                  <div className={cn(
                    "w-12 h-12 rounded-2xl flex items-center justify-center transition-all",
                    selectedId === patient.subject_id 
                      ? "bg-blue-600 text-white shadow-lg shadow-blue-200" 
                      : "bg-slate-100 dark:bg-slate-800 text-slate-400 group-hover:bg-blue-50 dark:group-hover:bg-blue-900/30 group-hover:text-blue-600",
                    patient.is_alert && "animate-pulse ring-4 ring-rose-500/50 ring-offset-2 dark:ring-offset-slate-950 bg-rose-600 text-white"
                  )}>
                    <User size={20} strokeWidth={2.5} />
                  </div>
                  {patient.is_alert && (
                    <div className="absolute -right-1 -top-1 w-3 h-3 bg-rose-500 rounded-full border-2 border-white dark:border-slate-950" />
                  )}
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-3">
                    <div className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
                      selectedId === patient.subject_id 
                        ? "bg-blue-600 text-white shadow-lg shadow-blue-400/30" 
                        : "bg-slate-100 dark:bg-slate-800 text-slate-400 group-hover:bg-blue-50 group-hover:text-blue-600",
                      patient.is_alert && "bg-rose-50 text-rose-600"
                    )}>
                      <User size={18} strokeWidth={2.5} />
                    </div>

                    <div className="text-right">
                      <div className={cn(
                        "text-lg font-mono font-black tracking-tighter",
                        patient.is_alert ? "text-rose-600" : (selectedId === patient.subject_id ? "text-blue-600" : "text-slate-700 dark:text-slate-200")
                      )}>
                        {patient.bpm}<span className="text-[8px] ml-0.5 opacity-50">BPM</span>
                      </div>
                      <div className={cn(
                        "text-[7px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full w-fit ml-auto border",
                        patient.is_alert ? "bg-rose-600 text-white border-rose-700 animate-pulse" : "bg-slate-100 dark:bg-slate-800 text-slate-400 border-transparent"
                      )}>
                        {patient.is_alert ? "⚠ Critical" : "Stable"}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-black text-slate-900 dark:text-slate-100 tracking-tight">
                        ID: PH-{patient.subject_id}
                      </span>
                      {patient.is_alert ? (
                        <ShieldAlert size={14} className="text-rose-500" />
                      ) : (
                        <ShieldCheck size={14} className="text-emerald-500" />
                      )}
                    </div>
                    <div className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest flex items-center gap-2">
                       <span>{patient.gender === "M" ? "MALE" : "FEMALE"}</span>
                       <span className="w-1 h-1 rounded-full bg-slate-300" />
                       <span>UNIT-0{patient.subject_id % 9}</span>
                    </div>
                    <div className={cn(
                      "text-[9px] font-black uppercase truncate mt-2 px-2.5 py-1.5 rounded-xl w-full text-center border transition-all",
                      patient.is_alert 
                        ? "animate-blink-red" 
                        : (selectedId === patient.subject_id 
                            ? "bg-blue-50 dark:bg-blue-900/30 text-blue-600 border-blue-100 dark:border-blue-800/50" 
                            : "bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 border-transparent")
                    )}>
                      {patient.diagnosis || "EVALUATION"}
                    </div>
                  </div>
                </>
              )}
            </motion.button>
          ))}
        </AnimatePresence>
        
        {filteredPatients.length === 0 && (
          <div className="py-12 text-center space-y-3">
             <div className="w-12 h-12 bg-slate-50 dark:bg-slate-950 rounded-2xl flex items-center justify-center mx-auto border border-slate-100 dark:border-slate-900">
                <Search size={20} className="text-slate-300" />
             </div>
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">No Patients Found</p>
          </div>
        )}
      </div>
    </aside>
  );
}
