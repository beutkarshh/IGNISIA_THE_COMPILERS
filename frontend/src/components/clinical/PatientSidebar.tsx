"use client";

import React, { useState } from "react";
import { User, ShieldCheck, ShieldAlert, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

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

export function PatientSidebar({ patients, selectedId, onSelect }: PatientSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "h-screen bg-[#F1F5F9]/30 dark:bg-slate-900/70 backdrop-blur-md border-r border-slate-200/60 dark:border-slate-800 flex flex-col gap-6 overflow-y-auto transition-[width,padding,background-color,border-color] duration-300",
        isCollapsed ? "w-24 p-4" : "w-80 p-6"
      )}
    >
      {/* Premium Header */}
      <div className={cn("mb-2 flex items-start", isCollapsed ? "justify-center" : "justify-between")}>
        {!isCollapsed && (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
              <h2 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight leading-none uppercase">ICU WARD</h2>
            </div>
            <p className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] px-4">Relational Clinical Registry</p>
          </div>
        )}

        <button
          type="button"
          onClick={() => setIsCollapsed((currentState) => !currentState)}
          className="shrink-0 w-10 h-10 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-200 hover:text-blue-600 hover:border-blue-200 dark:hover:border-blue-700 transition-all flex items-center justify-center"
          aria-label={isCollapsed ? "Expand patient sidebar" : "Collapse patient sidebar"}
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </button>
      </div>

      <div className={cn("flex flex-col", isCollapsed ? "gap-3" : "gap-4")}>
        {patients.map((patient, idx) => (
          <motion.button
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05 }}
            key={patient.subject_id}
            onClick={() => onSelect(patient.subject_id)}
            className={cn(
              "w-full rounded-3xl transition-all duration-300 relative group border",
              isCollapsed ? "p-3 flex items-center justify-center" : "p-5 text-left",
              selectedId === patient.subject_id
                ? "bg-white dark:bg-slate-800 shadow-[0_20px_50px_rgba(37,99,235,0.12)] border-blue-200/50 dark:border-blue-700/40 scale-[1.02] ring-1 ring-blue-50/70 dark:ring-blue-700/20"
                : "bg-white/40 dark:bg-slate-900/40 border-transparent hover:bg-white dark:hover:bg-slate-800/80 hover:border-slate-200/60 dark:hover:border-slate-700/60 hover:shadow-lg"
            )}
          >
            {/* Status Indicator */}
            {selectedId === patient.subject_id && !isCollapsed && (
              <motion.div
                layoutId="active-indicator"
                className="absolute -left-1 top-1/2 -translate-y-1/2 w-2 h-8 bg-blue-600 rounded-full"
              />
            )}

            {isCollapsed ? (
              <div className="relative">
                <div className={cn(
                  "w-12 h-12 rounded-2xl flex items-center justify-center transition-colors",
                  selectedId === patient.subject_id ? "bg-blue-600 text-white" : "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-300 group-hover:bg-blue-50 dark:group-hover:bg-blue-500/20 group-hover:text-blue-600 dark:group-hover:text-blue-300"
                )}>
                  <User size={24} strokeWidth={2.5} />
                </div>
                <span
                  className={cn(
                    "absolute -right-1 -top-1 w-3 h-3 rounded-full border-2 border-white dark:border-slate-900",
                    patient.is_alert ? "bg-rose-500" : "bg-emerald-500"
                  )}
                />
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <div className={cn(
                    "w-12 h-12 rounded-2xl flex items-center justify-center transition-colors",
                    selectedId === patient.subject_id ? "bg-blue-600 text-white" : "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-300 group-hover:bg-blue-50 dark:group-hover:bg-blue-500/20 group-hover:text-blue-600 dark:group-hover:text-blue-300"
                  )}>
                    <User size={24} strokeWidth={2.5} />
                  </div>

                  <div className="text-right">
                    <div className={cn(
                      "text-xl font-mono font-black tracking-tighter transition-colors",
                      patient.is_alert ? "text-rose-600 animate-pulse" : (selectedId === patient.subject_id ? "text-blue-700 dark:text-blue-300" : "text-slate-700 dark:text-slate-200")
                    )}>
                      {patient.bpm}<span className="text-[10px] ml-0.5 opacity-60">BPM</span>
                    </div>
                    <div className={cn(
                      "text-[8px] font-black uppercase tracking-widest mt-0.5",
                      patient.is_alert ? "text-rose-500" : "text-slate-400 dark:text-slate-500"
                    )}>
                      {patient.is_alert ? "Critical" : "Stable Pulse"}
                    </div>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-black text-slate-900 dark:text-slate-100 tracking-tight leading-none">
                      PH-{patient.subject_id}
                    </span>
                    {patient.is_alert ? (
                      <ShieldAlert size={14} className="text-rose-500" />
                    ) : (
                      <ShieldCheck size={14} className="text-emerald-500" />
                    )}
                  </div>
                  <div className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                    Gender: {patient.gender} • Bed 0A
                  </div>
                  <div className={cn(
                    "text-[10px] font-black uppercase truncate mt-2 px-2 py-1 rounded-lg w-fit",
                    selectedId === patient.subject_id ? "bg-blue-50 dark:bg-blue-500/15 text-blue-600 dark:text-blue-300" : "bg-slate-100/50 dark:bg-slate-800 text-slate-500 dark:text-slate-300"
                  )}>
                    {patient.diagnosis || "EVALUATION"}
                  </div>
                </div>
              </>
            )}
          </motion.button>
        ))}
      </div>
    </aside>
  );
}
