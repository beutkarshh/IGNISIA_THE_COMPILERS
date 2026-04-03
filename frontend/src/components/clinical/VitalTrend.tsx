"use client";

import React from "react";
import { motion } from "framer-motion";
import { VitalRecord } from "@/hooks/useClinicalStream";

interface VitalTrendProps {
  data: VitalRecord[];
  color?: string;
  label: string;
  unit: string;
}

export function VitalTrend({ data, color = "#3b82f6", label, unit }: VitalTrendProps) {
  if (data.length === 0) return (
    <div className="h-32 flex items-center justify-center text-slate-400 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
      Waiting for Patient Pulse...
    </div>
  );

  const lastValue = data[data.length - 1].valuenum;
  const isCritical = data[data.length - 1].is_outlier;

  // Chart Mapping
  const width = 300;
  const height = 100;
  const maxVal = Math.max(...data.map(d => d.valuenum)) * 1.2;
  const minVal = Math.min(...data.map(d => d.valuenum)) * 0.8;
  const range = maxVal - minVal || 1;

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((d.valuenum - minVal) / range) * height;
    return `${x},${y}`;
  }).join(" ");

  return (
    <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm transition-all hover:shadow-md">
      <div className="flex justify-between items-end mb-4">
        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{label}</span>
          <div className="flex items-baseline gap-1">
            <span className={`text-3xl font-bold font-mono tracking-tighter ${isCritical ? 'text-rose-500 animate-pulse' : 'text-slate-900'}`}>
              {lastValue.toFixed(0)}
            </span>
            <span className="text-sm font-medium text-slate-400">{unit}</span>
          </div>
        </div>
        <div className={`px-2 py-1 rounded-full text-[10px] font-bold ${isCritical ? 'bg-rose-100 text-rose-600' : 'bg-emerald-100 text-emerald-600'}`}>
          {isCritical ? "ALERT" : "STABLE"}
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-24 overflow-visible">
        {/* Shadow Path */}
        <motion.polyline
          fill="none"
          stroke={isCritical ? "#f43f5e" : color}
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
          initial={false}
          animate={{ points }}
          transition={{ duration: 0.1, ease: "linear" }}
          style={{ opacity: 0.15 }}
        />
        {/* Main Path */}
        <motion.polyline
          fill="none"
          stroke={isCritical ? "#f43f5e" : color}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
          initial={false}
          animate={{ points }}
          transition={{ duration: 0.1, ease: "linear" }}
        />
      </svg>
    </div>
  );
}
