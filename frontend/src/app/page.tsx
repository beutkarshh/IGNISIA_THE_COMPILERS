"use client";

import React, { useState, useEffect } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import Link from "next/link";
import { 
  Activity, ShieldAlert, Network, FileText, 
  Database, ArrowRight, Sun, SunMoon, 
  GitMerge, BrainCircuit, CheckCircle2, Lock
} from "lucide-react";
import { cn } from "@/lib/utils";

// --- Components ---

const ThemeToggle = ({ theme, toggleTheme }: { theme: string, toggleTheme: () => void }) => (
  <button
    onClick={toggleTheme}
    className="w-10 h-10 flex items-center justify-center bg-slate-100 dark:bg-slate-900 rounded-full border border-slate-200 dark:border-slate-800 shadow-sm hover:scale-105 transition-all text-slate-600 dark:text-slate-300 z-50"
  >
    {theme === "dark" ? <Sun size={18} className="text-amber-500" /> : <SunMoon size={18} className="text-blue-600" />}
  </button>
);

const ParticleNetwork = () => {
  // A simple Framer Motion based particle network effect for the background
  const particles = Array.from({ length: 40 });
  
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-40 dark:opacity-20 flex items-center justify-center">
      {particles.map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1.5 h-1.5 bg-blue-500/50 rounded-full"
          initial={{
            x: Math.random() * (typeof window !== "undefined" ? window.innerWidth : 1000) - 500,
            y: Math.random() * (typeof window !== "undefined" ? window.innerHeight : 1000) - 500,
            scale: Math.random() * 0.5 + 0.5,
          }}
          animate={{
            x: Math.random() * (typeof window !== "undefined" ? window.innerWidth : 1000) - 500,
            y: Math.random() * (typeof window !== "undefined" ? window.innerHeight : 1000) - 500,
          }}
          transition={{
            duration: Math.random() * 20 + 20,
            repeat: Infinity,
            repeatType: "reverse",
            ease: "linear",
          }}
        />
      ))}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-50/50 to-slate-50 dark:via-[#020617]/80 dark:to-[#020617]" />
    </div>
  );
};

export default function LandingPage() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [mounted, setMounted] = useState(false);
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);

  useEffect(() => {
    setMounted(true);
    const saved = window.localStorage.getItem("clinical-monitor-theme") as "light" | "dark" | null;
    if (saved) {
      setTheme(saved);
    } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      setTheme("dark");
    }
  }, []);

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

  const toggleTheme = () => setTheme(prev => prev === "dark" ? "light" : "dark");

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#020617] text-slate-900 dark:text-slate-50 font-sans selection:bg-blue-500/30 overflow-x-hidden transition-colors duration-500">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-white/60 dark:bg-[#020617]/60 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-600/20">
              <Activity size={24} />
            </div>
            <div>
              <h1 className="text-lg font-black tracking-tighter leading-tight">IGNISIA <span className="text-blue-600">AI</span></h1>
              <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Diagnostic Risk Assistant</p>
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
            <Link 
              href="/login"
              className="px-6 py-2.5 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm font-bold uppercase tracking-wider hover:scale-105 transition-transform flex items-center gap-2 shadow-xl shadow-slate-900/10 dark:shadow-white/10"
            >
              <Lock size={16} /> Access Portal
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex flex-col justify-center pt-20 overflow-hidden">
        <ParticleNetwork />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="flex flex-col gap-6"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400 w-fit">
              <div className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
              <span className="text-xs font-bold uppercase tracking-widest">Life-Saving Intervention</span>
            </div>
            
            <h1 className="text-5xl lg:text-7xl font-black tracking-tighter leading-[1.1]">
              Predicting ICU Risks <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-500">Before They Are Fatal.</span>
            </h1>
            
            <p className="text-lg text-slate-600 dark:text-slate-400 font-medium max-w-xl leading-relaxed">
              In fast-paced ICU environments, signals get lost in shift changes. Our multi-agent intelligence synthesizes unstructured notes, temporal labs, and clinical guidelines to alert doctors of sepsis and organ failure hours ahead of time.
            </p>
            
            <div className="flex flex-wrap items-center gap-4 mt-4">
              <Link href="/login" className="px-8 py-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold uppercase tracking-wider transition-colors flex items-center gap-2 shadow-xl shadow-blue-500/30">
                Launch Dashboard <ArrowRight size={18} />
              </Link>
              <a href="#pipeline" className="px-8 py-4 rounded-xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-900 dark:text-white font-bold uppercase tracking-wider transition-colors">
                How It Works
              </a>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.2 }}
            className="relative"
            style={{ y }}
          >
            {/* Abstract UI Representation */}
            <div className="relative w-full aspect-square md:aspect-[4/3] rounded-[2rem] border border-white/20 bg-white/40 dark:bg-slate-900/40 backdrop-blur-3xl shadow-2xl overflow-hidden p-6 gap-4 flex flex-col">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
                <div className="flex items-center gap-2">
                  <Activity className="text-blue-500" size={20} />
                  <span className="font-mono text-sm font-bold">SYNTHESIS_ENGINE</span>
                </div>
                <div className="px-3 py-1 bg-rose-500/20 text-rose-500 text-[10px] font-black uppercase tracking-widest rounded-lg animate-pulse">
                  Anomaly Detected
                </div>
              </div>
              
              <div className="flex-1 flex gap-4">
                {/* Agent Nodes */}
                <div className="w-1/3 flex flex-col justify-between p-4 rounded-xl bg-white/50 dark:bg-black/50 border border-slate-200 dark:border-slate-800">
                  <FileText className="text-slate-500 mb-2" size={20} />
                  <div className="h-2 w-full bg-slate-200 dark:bg-slate-800 rounded mb-2" />
                  <div className="h-2 w-2/3 bg-slate-200 dark:bg-slate-800 rounded" />
                </div>
                <div className="w-2/3 relative flex flex-col items-center justify-center p-4 rounded-xl bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20">
                  <Network className="text-blue-500 absolute top-4 left-4 opacity-50" size={100} />
                  <div className="relative z-10 text-center">
                     <span className="text-4xl font-black text-slate-800 dark:text-white">84%</span>
                     <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Sepsis Probability</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Glowing Orbs behind the UI */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3/4 h-3/4 bg-blue-500/30 blur-[100px] -z-10 rounded-full" />
            <div className="absolute bottom-0 right-0 w-1/2 h-1/2 bg-cyan-500/20 blur-[80px] -z-10 rounded-full" />
          </motion.div>
        </div>
      </section>

      {/* Multi-Agent Pipeline Section */}
      <section id="pipeline" className="py-32 relative z-10 bg-white dark:bg-[#060B19] border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-20">
            <h2 className="text-[10px] font-black text-blue-600 uppercase tracking-[0.3em] mb-4">Under The Hood</h2>
            <h3 className="text-3xl md:text-5xl font-black tracking-tight mb-6">Autonomous Multi-Agent Collaboration</h3>
            <p className="text-slate-600 dark:text-slate-400 text-lg">Four highly specialized AI agents working in continuous parallel to ensure no clinical signal is ignored.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: FileText, title: "Note Parser Agent", desc: "Extracts symptom histories and subtle cues from unstructured clinical notes written across different shifts.", color: "text-blue-500" },
              { icon: GitMerge, title: "Temporal Lab Mapper", desc: "Maps shifting lab anomalies (WBC, lactate) into a precise chronological timeline.", color: "text-cyan-500" },
              { icon: Database, title: "Guideline RAG", desc: "Cross-references patient patterns against thousands of standard medical guidelines in real-time.", color: "text-indigo-500" },
              { icon: BrainCircuit, title: "Chief Synthesis", desc: "Integrates all outputs into a unified diagnostic risk report and flags contradictory lab errors.", color: "text-rose-500" }
            ].map((agent, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="p-8 rounded-[2rem] bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
              >
                <div className={`w-12 h-12 rounded-xl bg-white dark:bg-[#020617] shadow-sm flex items-center justify-center mb-6 border border-slate-100 dark:border-slate-800 ${agent.color}`}>
                  <agent.icon size={24} />
                </div>
                <h4 className="text-xl font-bold mb-3">{agent.title}</h4>
                <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">{agent.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Safety & Outlier Detection */}
      <section className="py-32 relative z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col lg:flex-row gap-16 items-center">
            <motion.div 
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="lg:w-1/2"
            >
              <div className="aspect-square md:aspect-video lg:aspect-square rounded-[3rem] bg-slate-900 dark:bg-[#060B19] border border-slate-800 p-8 lg:p-12 relative overflow-hidden flex flex-col justify-between">
                <div>
                  <ShieldAlert className="text-rose-500 mb-6" size={40} />
                  <h4 className="text-white text-2xl font-black mb-2">Lab Error Rejected</h4>
                  <p className="text-slate-400 font-mono text-sm max-w-sm border-l-2 border-slate-700 pl-4 py-2">
                    "Incoming WBC reading of 2.1k/uL contradicts 3 days of steady 11.5k/uL data. Probable draw error. Redraw required. Risk report unaltered."
                  </p>
                </div>
                
                <div className="space-y-3">
                  {[
                    "Timeline Integrity Preserved",
                    "Do NO Harm Architecture",
                    "False Positive Reduction"
                  ].map((feat, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <CheckCircle2 className="text-emerald-500" size={20} />
                      <span className="text-slate-300 text-sm font-bold uppercase tracking-wider">{feat}</span>
                    </div>
                  ))}
                </div>
                
                <div className="absolute -bottom-20 -right-20 w-64 h-64 bg-rose-500/20 blur-[80px] rounded-full point-events-none" />
              </div>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="lg:w-1/2 space-y-6"
            >
              <h2 className="text-[10px] font-black text-rose-500 uppercase tracking-[0.3em]">Patient Safety First</h2>
              <h3 className="text-4xl md:text-5xl font-black tracking-tight leading-[1.1]">The System Knows <br/>When To Suspect Humans.</h3>
              <p className="text-xl text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                Our Chief Synthesis Agent constantly monitors incoming data against historical trends. 
              </p>
              <p className="text-lg text-slate-600 dark:text-slate-400 leading-relaxed">
                If a new lab result is a statistical outlier that contradicts days of reliable data, it isn't blindly accepted. The AI flags it as a probable error, refusing to alter the patient's diagnostic risk until a confirmed redraw is received. 
                <br/><br/>
                <strong className="text-slate-900 dark:text-white">This maintains diagnostic integrity and vastly reduces alarm fatigue.</strong>
              </p>
            </motion.div>
          </div>
        </div>
      </section>
      
      {/* Footer / CTA */}
      <footer className="py-20 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-[#060B19] text-center px-6">
        <h2 className="text-3xl font-black mb-8">Ready to explore the dashboard?</h2>
        <Link href="/login" className="inline-flex items-center gap-3 px-10 py-5 rounded-2xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-black uppercase tracking-widest hover:scale-105 transition-transform shadow-2xl">
          <Lock size={20} /> Enter Sandbox
        </Link>
        <p className="mt-12 text-sm text-slate-500 uppercase tracking-widest font-bold">
           Decision Support Only. Not for Clinical Diagnosis.
        </p>
      </footer>
    </div>
  );
}
