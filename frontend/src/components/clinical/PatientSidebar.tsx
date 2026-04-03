"use client";

import React from "react";
import { User, Activity, ShieldCheck, ShieldAlert } from "lucide-react";
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
  return (
    <div className="w-80 h-screen bg-[#F1F5F9]/30 backdrop-blur-md border-r border-slate-200/60 flex flex-col p-6 gap-6 overflow-y-auto">
      {/* Premium Header */}
      <div className="mb-2">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
          <h2 className="text-2xl font-black text-slate-900 tracking-tight leading-none uppercase">ICU WARD</h2>
        </div>
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] px-4">Relational Clinical Registry</p>
      </div>

      <div className="flex flex-col gap-4">
        {patients.map((patient, idx) => (
          <motion.button
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05 }}
            key={patient.subject_id}
            onClick={() => onSelect(patient.subject_id)}
            className={cn(
              "w-full text-left rounded-3xl p-5 transition-all duration-300 relative group border",
              selectedId === patient.subject_id 
                ? "bg-white shadow-[0_20px_50px_rgba(37,99,235,0.12)] border-blue-200/50 scale-[1.02] ring-1 ring-blue-50" 
                : "bg-white/40 border-transparent hover:bg-white hover:border-slate-200/60 hover:shadow-lg"
            )}
          >
            {/* Status Indicator */}
            {selectedId === patient.subject_id && (
              <motion.div 
                layoutId="active-indicator"
                className="absolute -left-1 top-1/2 -translate-y-1/2 w-2 h-8 bg-blue-600 rounded-full" 
              />
            )}

            <div className="flex items-center justify-between mb-4">
              <div className={cn(
                "w-12 h-12 rounded-2xl flex items-center justify-center transition-colors",
                selectedId === patient.subject_id ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-400 group-hover:bg-blue-50 group-hover:text-blue-600"
              )}>
                <User size={24} strokeWidth={2.5} />
              </div>
              
              <div className="text-right">
                <div className={cn(
                  "text-xl font-mono font-black tracking-tighter transition-colors",
                  patient.is_alert ? "text-rose-600 animate-pulse" : (selectedId === patient.subject_id ? "text-blue-700" : "text-slate-700")
                )}>
                  {patient.bpm}<span className="text-[10px] ml-0.5 opacity-60">BPM</span>
                </div>
                <div className={cn(
                  "text-[8px] font-black uppercase tracking-widest mt-0.5",
                  patient.is_alert ? "text-rose-500" : "text-slate-400"
                )}>
                  {patient.is_alert ? "Critical" : "Stable Pulse"}
                </div>
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-black text-slate-900 tracking-tight leading-none">
                  PH-{patient.subject_id}
                </span>
                {patient.is_alert ? (
                  <ShieldAlert size={14} className="text-rose-500" />
                ) : (
                  <ShieldCheck size={14} className="text-emerald-500" />
                )}
              </div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Gender: {patient.gender} • Bed 0A
              </div>
              <div className={cn(
                "text-[10px] font-black uppercase truncate mt-2 px-2 py-1 rounded-lg w-fit",
                selectedId === patient.subject_id ? "bg-blue-50 text-blue-600" : "bg-slate-100/50 text-slate-500"
              )}>
                {patient.diagnosis || "EVALUATION"}
              </div>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
