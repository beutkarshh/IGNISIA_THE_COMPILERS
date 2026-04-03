"use client";

import React from "react";
import { User, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

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
    <div className="w-80 h-screen bg-slate-50/50 border-r border-slate-200 flex flex-col p-4 gap-4 overflow-y-auto">
      <div className="flex items-center justify-between mb-2 px-2">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">ICU WARD</h2>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Active Bedside Monitors</p>
        </div>
        <div className="bg-blue-600 text-white px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-wider shadow-lg shadow-blue-500/20">LIVE</div>
      </div>

      <div className="space-y-3">
        {patients.map((patient) => (
          <button
            key={patient.subject_id}
            onClick={() => onSelect(patient.subject_id)}
            className={cn(
              "w-full p-5 rounded-2xl flex items-center justify-between transition-all group border text-left",
              selectedId === patient.subject_id 
                ? "bg-white border-blue-200 shadow-xl shadow-blue-500/10 ring-1 ring-blue-50" 
                : "bg-transparent border-transparent hover:bg-white hover:border-slate-100"
            )}
          >
            <div className="flex items-center gap-4">
              <div className={cn(
                "w-12 h-12 rounded-2xl flex items-center justify-center transition-all shadow-sm",
                selectedId === patient.subject_id ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-500 group-hover:bg-blue-100 group-hover:text-blue-600"
              )}>
                <User size={24} />
              </div>
              <div className="overflow-hidden">
                <div className="font-black text-slate-800 text-base leading-none mb-1 tracking-tighter uppercase whitespace-nowrap overflow-hidden text-ellipsis">
                  {patient.subject_id}
                </div>
                <div className="text-[10px] text-slate-400 flex items-center gap-1 font-black uppercase tracking-wider">
                  Gender: {patient.gender} • BED-0A
                </div>
                <div className="text-[10px] text-blue-500 font-bold uppercase truncate mt-1">
                  {patient.diagnosis || "ADMISSION EVAL"}
                </div>
              </div>
            </div>

            <div className="flex flex-col items-end shrink-0">
              <div className="flex items-center gap-1 text-slate-400">
                <Activity size={16} className={cn(patient.is_alert && 'text-rose-500 animate-pulse')} />
                <span className={cn("text-xl font-black font-mono tracking-tighter leading-none", patient.is_alert ? 'text-rose-600' : 'text-slate-700')}>
                  {patient.bpm}
                </span>
              </div>
              <div className={cn(
                "text-[8px] font-black uppercase tracking-widest mt-1 px-1.5 py-0.5 rounded",
                patient.is_alert ? 'bg-rose-100 text-rose-600' : 'bg-slate-100 text-slate-500'
              )}>
                {patient.is_alert ? "CRITICAL" : "STABLE"}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
