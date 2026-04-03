"use client";

import React, { useMemo } from "react";
import { motion } from "framer-motion";
import { Activity, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface DataPoint {
  valuenum: number;
  charttime: string;
}

interface VitalTrendProps {
  label: string;
  unit: string;
  color: string;
  data: DataPoint[];
  className?: string;
}

export function VitalTrend({ label, unit, color, data, className }: VitalTrendProps) {
  const points = useMemo(() => {
    if (data.length < 2) return "";
    const width = 400;
    const height = 100;
    const max = Math.max(...data.map(d => d.valuenum)) * 1.1;
    const min = Math.min(...data.map(d => d.valuenum)) * 0.9;
    const range = max - min;

    return data
      .map((d, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - ((d.valuenum - min) / (range || 1)) * height;
        return `${x},${y}`;
      })
      .join(" ");
  }, [data]);

  const latestVal = data.length > 0 ? data[data.length - 1].valuenum : 0;
  const prevVal = data.length > 1 ? data[data.length - 2].valuenum : 0;
  const isUp = latestVal > prevVal;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        "bg-white/60 dark:bg-slate-900/70 backdrop-blur-md rounded-[2.5rem] p-8 border border-white/20 dark:border-slate-800 shadow-xl shadow-slate-200/20 dark:shadow-black/25 group hover:shadow-2xl transition-all duration-500",
        className
      )}
    >
      <div className="flex justify-between items-start mb-8">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center group-hover:bg-blue-600 transition-colors duration-500">
            <Activity className="text-slate-400 dark:text-slate-300 group-hover:text-white transition-colors duration-500" size={24} />
          </div>
          <div>
            <h3 className="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em]">{label}</h3>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-black text-slate-900 dark:text-slate-100 tracking-tighter leading-none">
                {latestVal.toFixed(1)}
              </span>
              <span className="text-sm font-black text-slate-400 dark:text-slate-500 uppercase opacity-60">{unit}</span>
            </div>
          </div>
        </div>
        
        <div className={cn(
          "flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest",
          isUp ? "bg-emerald-50 dark:bg-emerald-500/15 text-emerald-600 dark:text-emerald-300" : "bg-rose-50 dark:bg-rose-500/15 text-rose-600 dark:text-rose-300"
        )}>
          {isUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {Math.abs(latestVal - prevVal).toFixed(1)} Delta
        </div>
      </div>

      <div className="relative h-24 w-full">
        <svg
          viewBox="0 0 400 100"
          className="w-full h-full overflow-visible"
          preserveAspectRatio="none"
        >
          {/* Waveform Shadow/Glow */}
          <motion.polyline
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
            style={{ opacity: 0.15, filter: 'blur(8px)' }}
          />
          
          {/* Main Waveform */}
          <motion.polyline
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
            fill="none"
            stroke={color}
            strokeWidth="3.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
            className="drop-shadow-[0_2px_10px_rgba(37,99,235,0.4)]"
          />
          
          {/* Pulse Indicator */}
          {data.length > 0 && (
            <motion.circle
              cx={(data.length - 1) / (data.length - 1) * 400 || 400}
              cy={100 - ((latestVal - Math.min(...data.map(d => d.valuenum) || [0]) * 0.9) / ((Math.max(...data.map(d => d.valuenum) || [100]) * 1.1 - Math.min(...data.map(d => d.valuenum) || [0]) * 0.9) || 1)) * 100}
              r="4"
              fill={color}
              className="animate-pulse pulse-glow"
            />
          )}
        </svg>

        {data.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[10px] font-black text-slate-300 dark:text-slate-500 uppercase tracking-[0.3em] flex items-center gap-2">
              <Activity className="animate-pulse" size={14} /> Waiting for Patient Pulse...
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
