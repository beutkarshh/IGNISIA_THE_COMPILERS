"use client";

import React, { useState, useEffect } from "react";
import { PatientSidebar } from "@/components/clinical/PatientSidebar";
import { SepsisBanner } from "@/components/clinical/SepsisBanner";
import { VitalTrend } from "@/components/clinical/VitalTrend";
import { useClinicalStream } from "@/hooks/useClinicalStream";
import { useClinicalData } from "@/hooks/useClinicalData";
import { Activity, Thermometer, Droplets, Wind } from "lucide-react";

export default function Home() {
  const { patients, isLoading: isLoadingDemographics } = useClinicalData();
  const [selectedId, setSelectedId] = useState<number | null>(null);

  // Sync selected ID with first patient once loaded
  useEffect(() => {
    if (patients.length > 0 && !selectedId) {
      setSelectedId(patients[0].subject_id);
    }
  }, [patients, selectedId]);

  const { vitals } = useClinicalStream(patients.map(p => p.subject_id));

  if (isLoadingDemographics || !selectedId) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-white text-slate-400 font-black uppercase tracking-widest">
        <Activity className="animate-pulse mr-2" /> Initializing Clinical Database...
      </div>
    );
  }

  const selectedPatient = patients.find(p => p.subject_id === selectedId)!;
  const currentVitals = vitals[selectedId] || [];
  
  // Real Clinical Logic
  const latestPulse = currentVitals.slice(-1)[0];
  const isAlert = latestPulse?.is_outlier || (latestPulse?.valuenum > 130);
  const sepsisProbability = isAlert ? 84 : 12; // This will later link to AI model inference
  const status = isAlert ? "critical" : "stable";

  return (
    <main className="flex h-screen bg-[#F8FAFC] overflow-hidden antialiased">
      {/* 1. Clinical Rail (Database Driven) */}
      <PatientSidebar 
        patients={patients.map(p => ({
          subject_id: p.subject_id,
          gender: p.gender,
          diagnosis: p.diagnosis,
          bpm: vitals[p.subject_id]?.slice(-1)[0]?.valuenum || 0,
          is_alert: vitals[p.subject_id]?.slice(-1)[0]?.is_outlier || false
        }))} 
        selectedId={selectedId} 
        onSelect={setSelectedId} 
      />

      {/* 2. Pure Data Workspace */}
      <div className="flex-1 p-8 overflow-y-auto space-y-8">
        <SepsisBanner 
          probability={sepsisProbability} 
          status={status} 
          lastCheck={new Date().toLocaleTimeString()} 
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <VitalTrend 
            label="Real-time Heart Rate (BPM)" 
            unit="BPM" 
            color="#2563EB" 
            data={currentVitals} // Currently showing all vitals, will add filtering in Ph 3
          />
          <VitalTrend 
            label="Sepsis Risk Markers" 
            unit="Delta" 
            color="#0EA5E9" 
            data={currentVitals} 
          />
        </div>

        {/* Clinical History Card */}
        <div className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-xl shadow-slate-200/20">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-xl font-black text-slate-800 uppercase tracking-tight flex items-center gap-2">
              <Activity className="text-blue-600" />
              Patient Case Study: {selectedId}
            </h3>
            <div className="px-4 py-2 bg-slate-100 rounded-xl text-xs font-black text-slate-500 uppercase tracking-widest">
              Relational Link: Admissions • Patients
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-slate-700">
            <div className="space-y-6">
              <div className="p-5 rounded-2xl bg-blue-50/50 border border-blue-100 text-sm font-bold leading-relaxed">
                "Clinical Admission Diagnosis: {selectedPatient.diagnosis}. Currently monitoring the patient for respiratory stability and sepsis onset markers."
              </div>
              <div className="space-y-3 px-2">
                <div className="flex justify-between border-b border-slate-100 pb-2">
                  <span className="text-xs font-black text-slate-400 uppercase tracking-wider">Subject ID</span>
                  <span className="text-sm font-black font-mono">{selectedPatient.subject_id}</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-2">
                  <span className="text-xs font-black text-slate-400 uppercase tracking-wider">Gender</span>
                  <span className="text-sm font-black uppercase">{selectedPatient.gender}</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-2">
                  <span className="text-xs font-black text-slate-400 uppercase tracking-wider">Admission Category</span>
                  <span className="text-sm font-black uppercase text-blue-600">{selectedPatient.admission_type}</span>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className="text-xs font-black uppercase tracking-widest text-slate-400">Clinical Protocol</h4>
              <div className="grid grid-cols-1 gap-3">
                {[
                  { label: "Sepsis Fluid Resuscitation", val: "N/A" },
                  { label: "Antibiotic Interval", val: "6H" },
                  { label: "Lab Draw Schedule", val: "BID" }
                ].map((item, idx) => (
                  <div key={idx} className="p-4 rounded-2xl border border-slate-100 flex items-center justify-between group hover:border-blue-200 transition-colors">
                    <span className="text-xs font-black uppercase tracking-tight text-slate-500 group-hover:text-blue-600">{item.label}</span>
                    <span className="text-xs font-black font-mono text-slate-400">{item.val}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
