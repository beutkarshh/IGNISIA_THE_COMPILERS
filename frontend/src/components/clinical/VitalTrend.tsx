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
  yMin?: number;   // optional fixed y-axis floor (e.g. 0, 40)
  yMax?: number;   // optional fixed y-axis ceiling (e.g. 200, 110)
}

const W = 400;
const H = 100;
const DISPLAY_POINTS = 30; // how many points to show in the scrolling window

export function VitalTrend({
  label, unit, color, data,
  className, yMin, yMax,
}: VitalTrendProps) {

  // Debug logging
  React.useEffect(() => {
    console.log(`[VitalTrend] ${label} received ${data.length} data points:`, data.slice(0, 3));
  }, [data, label]);

  // Scrolling window — always show last DISPLAY_POINTS values
  const window = useMemo(
    () => data.slice(-DISPLAY_POINTS),
    [data]
  );

  const { polylinePoints, areaPath, yLabels, gridYs, latestY, dotX } = useMemo(() => {
    if (window.length < 2) {
      return { polylinePoints: "", areaPath: "", yLabels: [], gridYs: [], latestY: H / 2, dotX: W };
    }

    // Filter out invalid values
    const validData = window.filter(d => 
      d.valuenum !== null && 
      d.valuenum !== undefined && 
      !isNaN(d.valuenum) && 
      isFinite(d.valuenum)
    );

    if (validData.length < 2) {
      return { polylinePoints: "", areaPath: "", yLabels: [], gridYs: [], latestY: H / 2, dotX: W };
    }

    const vals = validData.map(d => d.valuenum);
    const rawMin = Math.min(...vals);
    const rawMax = Math.max(...vals);
    const padding = (rawMax - rawMin) * 0.25 || 5;

    // Y scale: fixed bounds if provided, else auto with padding
    const lo = yMin !== undefined ? yMin : rawMin - padding;
    const hi = yMax !== undefined ? yMax : rawMax + padding;
    const range = hi - lo || 1;

    // X: spread evenly across full width (scrolling feel — newest = rightmost)
    const toX = (i: number) => (i / (validData.length - 1)) * W;
    const toY = (v: number) => H - ((v - lo) / range) * (H - 4) - 2;

    // Smooth polyline points
    const pts = validData.map((d, i) => `${toX(i)},${toY(d.valuenum)}`).join(" ");

    // Filled area path
    const firstX = toX(0);
    const lastX  = toX(validData.length - 1);
    const area = `M${firstX},${H} ` + validData.map((d, i) => `L${toX(i)},${toY(d.valuenum)}`).join(" ") + ` L${lastX},${H} Z`;

    // Y-axis: 3 labels (top, mid, bottom)
    const mid = (lo + hi) / 2;
    const labels = [
      { v: hi,  y: 4 },
      { v: mid, y: H / 2 + 2 },
      { v: lo,  y: H - 4 },
    ];

    // Grid lines at the same 3 positions
    const grids = [4, H / 2, H - 4];

    // Dot for latest point
    const last = validData[validData.length - 1];
    const latestYPos = toY(last.valuenum);

    return {
      polylinePoints: pts,
      areaPath: area,
      yLabels: labels,
      gridYs: grids,
      latestY: latestYPos,
      dotX: toX(validData.length - 1),
    };
  }, [window, yMin, yMax]);

  const latestVal = data.length > 0 && data[data.length - 1]?.valuenum != null && !isNaN(data[data.length - 1].valuenum) 
    ? data[data.length - 1].valuenum 
    : 0;
  const prevVal = data.length > 1 && data[data.length - 2]?.valuenum != null && !isNaN(data[data.length - 2].valuenum)
    ? data[data.length - 2].valuenum 
    : 0;
  const delta = latestVal - prevVal;
  const isUp = delta >= 0;

  // Gradient id (unique per color to avoid SVG conflicts)
  const gradId = `vt-grad-${color.replace(/[^a-zA-Z0-9]/g, "")}`;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        "bg-white/60 dark:bg-slate-900/70 backdrop-blur-md rounded-[2.5rem] p-8 border border-white/20 dark:border-slate-800 shadow-xl shadow-slate-200/20 dark:shadow-black/25 group hover:shadow-2xl transition-all duration-500",
        className
      )}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
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
          isUp
            ? "bg-emerald-50 dark:bg-emerald-500/15 text-emerald-600 dark:text-emerald-300"
            : "bg-rose-50 dark:bg-rose-500/15 text-rose-600 dark:text-rose-300"
        )}>
          {isUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {Math.abs(delta).toFixed(1)} Delta
        </div>
      </div>

      {/* Chart area */}
      <div className="relative" style={{ height: 120 }}>
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-0 w-10 flex flex-col justify-between pointer-events-none z-10">
          {yLabels.map((l, i) => (
            <span key={i} className="text-[9px] font-black text-slate-300 dark:text-slate-600 leading-none">
              {Number.isInteger(l.v) ? l.v : l.v.toFixed(0)}
            </span>
          ))}
        </div>

        {/* SVG graph — offset by y-axis label width */}
        <div className="absolute left-10 right-0 top-0 bottom-0">
          {data.length < 2 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-[10px] font-black text-slate-300 dark:text-slate-500 uppercase tracking-[0.3em] flex items-center gap-2">
                <Activity className="animate-pulse" size={14} /> Waiting for Patient Pulse...
              </span>
            </div>
          ) : (
            <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full overflow-visible" preserveAspectRatio="none">
              <defs>
                <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity="0.25" />
                  <stop offset="100%" stopColor={color} stopOpacity="0.01" />
                </linearGradient>
              </defs>

              {/* Horizontal grid lines */}
              {gridYs.map((y, i) => (
                <line
                  key={i}
                  x1={0} y1={y} x2={W} y2={y}
                  stroke="currentColor"
                  strokeWidth="0.5"
                  strokeDasharray="4 4"
                  className="text-slate-200 dark:text-slate-700"
                  opacity={0.8}
                />
              ))}

              {/* Filled area */}
              <motion.path
                d={areaPath}
                fill={`url(#${gradId})`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.6 }}
              />

              {/* Glow shadow */}
              <polyline
                points={polylinePoints}
                fill="none"
                stroke={color}
                strokeWidth="8"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ opacity: 0.12, filter: "blur(7px)" }}
              />

              {/* Main line */}
              <motion.polyline
                key={data.length} // re-animate on new data
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                fill="none"
                stroke={color}
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={polylinePoints}
                style={{ filter: `drop-shadow(0 2px 8px ${color}60)` }}
              />

              {/* Live dot at latest value - only render if we have valid coordinates */}
              {!isNaN(dotX) && !isNaN(latestY) && isFinite(dotX) && isFinite(latestY) && (
                <motion.circle
                  cx={dotX}
                  cy={latestY}
                  r={5}
                  fill={color}
                  animate={{ r: [4, 6, 4], opacity: [1, 0.6, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                  style={{ filter: `drop-shadow(0 0 6px ${color})` }}
                />
              )}
            </svg>
          )}
        </div>
      </div>
    </motion.div>
  );
}
