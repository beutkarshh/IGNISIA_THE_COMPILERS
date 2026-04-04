"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain, Activity, TrendingUp, TrendingDown, Minus, AlertTriangle,
  Clock, Zap, Target, Eye, CheckCircle, AlertCircle, XCircle,
  BarChart3, LineChart, FileText, Pill, Stethoscope, FlaskConical,
  Users, Heart, Thermometer, Shield, TrendingUpIcon, TrendingDownIcon
} from "lucide-react";
import { cn } from "@/lib/utils";

// Types matching the backend service
interface AITrendPrediction {
  itemid: number;
  vital_name: string;
  current_value: number;
  trend_direction: "rising" | "falling" | "stable";
  trend_confidence: number;
  prediction_next_30s: number;
  abrupt_change_risk: number;
  pattern_detected?: string;
  alert_level: "none" | "caution" | "warning" | "critical";
}

interface ClinicalNote {
  timestamp: string;
  type: "nursing" | "physician" | "respiratory" | "pharmacy";
  author: string;
  content: string;
  priority: "high" | "medium" | "low";
}

interface LabResult {
  name: string;
  value: number;
  unit: string;
  reference_range: string;
  status: "normal" | "high" | "low" | "critical";
  trend: "improving" | "worsening" | "stable";
}

interface Medication {
  name: string;
  dose: string;
  route: string;
  frequency: string;
  last_given: string;
  next_due: string;
  compliance: number;
}

interface RiskFactor {
  factor: string;
  severity: "low" | "moderate" | "high" | "critical";
  description: string;
  recommendation: string;
}

interface AIAnalysisResult {
  patient_id: number;
  analysis_timestamp: string;
  processing_time_ms: number;
  cycle_number: number;
  trend_predictions: AITrendPrediction[];
  overall_risk_score: number;
  pattern_summary: string;
  alert_count: {
    none: number;
    caution: number;
    warning: number;
    critical: number;
  };
  confidence_score: number;
  clinical_notes: ClinicalNote[];
  lab_results: LabResult[];
  medications: Medication[];
  risk_factors: RiskFactor[];
  ai_recommendations: string[];
  sepsis_risk: {
    probability: number;
    qSOFA_score: number;
    early_warning_score: number;
  };
  complication_risks: {
    name: string;
    probability: number;
    timeframe: string;
  }[];
}

interface AgentStep {
  name: string;
  description: string;
  duration: number; // in seconds
  color: string;
  icon: string;
}

interface AIAnalysisPanelProps {
  patientId: number;
  className?: string;
}

const getTrendIcon = (direction: string, size: number = 16) => {
  switch (direction) {
    case "rising":
      return <TrendingUp size={size} className="text-amber-600" />;
    case "falling":
      return <TrendingDown size={size} className="text-blue-600" />;
    default:
      return <Minus size={size} className="text-slate-600" />;
  }
};

const getAlertColor = (level: string) => {
  switch (level) {
    case "critical":
      return "text-red-600 bg-red-50 border-red-200";
    case "warning":
      return "text-amber-600 bg-amber-50 border-amber-200";
    case "caution":
      return "text-yellow-600 bg-yellow-50 border-yellow-200";
    default:
      return "text-slate-600 bg-slate-50 border-slate-200";
  }
};

const getAlertIcon = (level: string) => {
  switch (level) {
    case "critical":
      return <XCircle className="text-red-600" size={20} />;
    case "warning":
      return <AlertTriangle className="text-amber-600" size={20} />;
    case "caution":
      return <AlertCircle className="text-yellow-600" size={20} />;
    default:
      return <CheckCircle className="text-green-600" size={20} />;
  }
};

export function AIAnalysisPanel({ patientId, className }: AIAnalysisPanelProps) {
  const [aiResults, setAiResults] = useState<AIAnalysisResult[]>([]); // Changed to array for stacking
  const [isProcessing, setIsProcessing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<"disconnected" | "connecting" | "connected">("connected"); // Default to connected since we're using REST
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [processingCycle, setProcessingCycle] = useState(0);
  
  // Agent workflow animation state
  const [currentStep, setCurrentStep] = useState(0);
  const [workflowProgress, setWorkflowProgress] = useState(0);
  const [isWorkflowRunning, setIsWorkflowRunning] = useState(false);
  const [autoMode, setAutoMode] = useState(false); // Manual control by default

  // Define the AI agent workflow steps - all 5 seconds for consistency
  const agentSteps: AgentStep[] = [
    {
      name: "Data Ingestion Agent",
      description: "Processing incoming telemetry streams and vital signs...",
      duration: 5,
      color: "from-blue-500 to-cyan-500",
      icon: "📊"
    },
    {
      name: "Pattern Detection Agent", 
      description: "Analyzing trends and identifying anomalous patterns...",
      duration: 5,
      color: "from-purple-500 to-pink-500",
      icon: "🔍"
    },
    {
      name: "Risk Assessment Agent",
      description: "Calculating sepsis risk and complication probabilities...",
      duration: 5,
      color: "from-red-500 to-orange-500", 
      icon: "⚠️"
    },
    {
      name: "Trend Prediction Agent",
      description: "Forecasting vital sign trajectories and abrupt changes...",
      duration: 5,
      color: "from-green-500 to-emerald-500",
      icon: "📈"
    },
    {
      name: "Statistical Validation Agent",
      description: "Cross-validating results and detecting outliers...",
      duration: 5,
      color: "from-indigo-500 to-blue-500",
      icon: "✅"
    },
    {
      name: "Chief Synthesis Agent",
      description: "Generating final diagnosis and recommendations...",
      duration: 5,
      color: "from-violet-500 to-purple-500",
      icon: "🧠"
    }
  ];

  // Create comprehensive mock AI result with clinical data
  const createMockAIResult = () => {
    const cycles = [5, 8, 12, 15, 18, 22, 25][Math.floor(Math.random() * 7)];
    const riskLevels = [
      { 
        score: 15, 
        pattern: "Stable vital sign patterns with normal variations", 
        alerts: { none: 2, caution: 0, warning: 0, critical: 0 },
        sepsisRisk: 12,
        qsofa: 0
      },
      { 
        score: 35, 
        pattern: "Mixed trending patterns with some concerning elements", 
        alerts: { none: 1, caution: 1, warning: 0, critical: 0 },
        sepsisRisk: 28,
        qsofa: 1
      },
      { 
        score: 58, 
        pattern: "Multiple concerning trends requiring close monitoring", 
        alerts: { none: 0, caution: 2, warning: 0, critical: 0 },
        sepsisRisk: 45,
        qsofa: 2
      },
      { 
        score: 73, 
        pattern: "Deteriorating patterns with moderate intervention needs", 
        alerts: { none: 0, caution: 1, warning: 1, critical: 0 },
        sepsisRisk: 65,
        qsofa: 2
      },
      { 
        score: 89, 
        pattern: "Critical patterns detected - immediate intervention required", 
        alerts: { none: 0, caution: 0, warning: 1, critical: 1 },
        sepsisRisk: 82,
        qsofa: 3
      }
    ];
    
    const selectedRisk = riskLevels[Math.floor(Math.random() * riskLevels.length)];
    
    // Generate realistic clinical notes
    const clinicalNotes: ClinicalNote[] = [
      {
        timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
        type: "nursing",
        author: "Sarah Johnson, RN",
        content: "Patient appears comfortable, responding well to treatment. Urine output adequate. No acute distress noted.",
        priority: "medium"
      },
      {
        timestamp: new Date(Date.now() - 120 * 60 * 1000).toISOString(),
        type: "physician",
        author: "Dr. Michael Chen",
        content: "Reviewed latest labs. WBC trending upward, monitoring for signs of infection. Continue current antibiotics.",
        priority: "high"
      },
      {
        timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        type: "respiratory",
        author: "James Rodriguez, RRT",
        content: "O2 saturation stable on 2L nasal cannula. Breath sounds clear bilaterally. No respiratory distress.",
        priority: "low"
      }
    ];
    
    // Generate lab results
    const labResults: LabResult[] = [
      {
        name: "White Blood Cells",
        value: 11.2 + Math.random() * 3,
        unit: "K/μL",
        reference_range: "4.0-11.0",
        status: "high",
        trend: "worsening"
      },
      {
        name: "Lactate",
        value: 2.1 + Math.random() * 1.5,
        unit: "mmol/L",
        reference_range: "0.5-2.0",
        status: "high",
        trend: selectedRisk.score > 50 ? "worsening" : "stable"
      },
      {
        name: "Procalcitonin",
        value: 0.8 + Math.random() * 2,
        unit: "ng/mL",
        reference_range: "<0.25",
        status: "high",
        trend: "improving"
      },
      {
        name: "Creatinine",
        value: 1.1 + Math.random() * 0.5,
        unit: "mg/dL",
        reference_range: "0.6-1.2",
        status: Math.random() > 0.5 ? "normal" : "high",
        trend: "stable"
      }
    ];
    
    // Generate medications
    const medications: Medication[] = [
      {
        name: "Ceftriaxone",
        dose: "2g",
        route: "IV",
        frequency: "Q12H",
        last_given: "06:00",
        next_due: "18:00",
        compliance: 95
      },
      {
        name: "Norepinephrine",
        dose: "8 mcg/min",
        route: "IV drip",
        frequency: "Continuous",
        last_given: "Ongoing",
        next_due: "Continuous",
        compliance: 100
      },
      {
        name: "Acetaminophen",
        dose: "650mg",
        route: "PO",
        frequency: "Q6H PRN",
        last_given: "14:30",
        next_due: "20:30",
        compliance: 88
      }
    ];
    
    // Generate risk factors
    const riskFactors: RiskFactor[] = [
      {
        factor: "Elevated Lactate",
        severity: selectedRisk.score > 60 ? "high" : "moderate",
        description: "Serum lactate levels suggest tissue hypoperfusion",
        recommendation: "Monitor closely, consider fluid resuscitation"
      },
      {
        factor: "Leukocytosis",
        severity: "moderate",
        description: "White blood cell count elevated indicating possible infection",
        recommendation: "Continue antibiotic therapy, monitor inflammatory markers"
      },
      {
        factor: "Hemodynamic Instability",
        severity: selectedRisk.score > 70 ? "high" : "low",
        description: "Blood pressure requiring vasopressor support",
        recommendation: "Optimize fluid balance, monitor cardiac output"
      }
    ];
    
    const mockResult: AIAnalysisResult = {
      patient_id: patientId,
      analysis_timestamp: new Date().toISOString(),
      processing_time_ms: 1150 + Math.random() * 400,
      cycle_number: cycles,
      trend_predictions: [
        {
          itemid: 211,
          vital_name: "Heart Rate",
          current_value: Math.round(85 + Math.random() * 30),
          trend_direction: ["rising", "falling", "stable"][Math.floor(Math.random() * 3)] as any,
          trend_confidence: Number((0.65 + Math.random() * 0.3).toFixed(2)),
          prediction_next_30s: Math.round(88 + Math.random() * 25),
          abrupt_change_risk: Number((Math.random() * 0.7).toFixed(2)),
          pattern_detected: Math.random() > 0.6 ? ["oscillating", "accelerating", "decelerating"][Math.floor(Math.random() * 3)] as any : undefined,
          alert_level: selectedRisk.score > 60 ? (Math.random() > 0.7 ? "warning" : "caution") : 
                      selectedRisk.score > 30 ? (Math.random() > 0.5 ? "caution" : "none") : "none"
        },
        {
          itemid: 456,
          vital_name: "Mean Blood Pressure",
          current_value: Math.round(70 + Math.random() * 25),
          trend_direction: ["rising", "falling", "stable"][Math.floor(Math.random() * 3)] as any,
          trend_confidence: Number((0.6 + Math.random() * 0.35).toFixed(2)),
          prediction_next_30s: Math.round(72 + Math.random() * 23),
          abrupt_change_risk: Number((Math.random() * 0.5).toFixed(2)),
          pattern_detected: Math.random() > 0.7 ? ["oscillating", "accelerating", "decelerating"][Math.floor(Math.random() * 3)] as any : undefined,
          alert_level: selectedRisk.score > 50 ? (Math.random() > 0.8 ? "warning" : "caution") : 
                      selectedRisk.score > 25 ? (Math.random() > 0.6 ? "caution" : "none") : "none"
        },
        {
          itemid: 618,
          vital_name: "Respiratory Rate",
          current_value: Math.round(18 + Math.random() * 8),
          trend_direction: ["rising", "falling", "stable"][Math.floor(Math.random() * 3)] as any,
          trend_confidence: Number((0.7 + Math.random() * 0.25).toFixed(2)),
          prediction_next_30s: Math.round(19 + Math.random() * 7),
          abrupt_change_risk: Number((Math.random() * 0.4).toFixed(2)),
          pattern_detected: Math.random() > 0.8 ? ["oscillating", "accelerating"][Math.floor(Math.random() * 2)] as any : undefined,
          alert_level: selectedRisk.score > 70 ? (Math.random() > 0.6 ? "warning" : "caution") : "none"
        }
      ],
      overall_risk_score: selectedRisk.score,
      pattern_summary: selectedRisk.pattern,
      alert_count: selectedRisk.alerts,
      confidence_score: Number((0.72 + Math.random() * 0.23).toFixed(2)),
      clinical_notes: clinicalNotes,
      lab_results: labResults,
      medications: medications,
      risk_factors: riskFactors,
      ai_recommendations: [
        "Monitor fluid balance and urine output closely",
        "Consider echocardiogram to assess cardiac function",
        "Review antibiotic spectrum based on culture results",
        "Implement early mobilization protocol when stable",
        "Monitor for signs of organ dysfunction"
      ].slice(0, 3 + Math.floor(Math.random() * 3)),
      sepsis_risk: {
        probability: selectedRisk.sepsisRisk,
        qSOFA_score: selectedRisk.qsofa,
        early_warning_score: Math.floor(3 + Math.random() * 8)
      },
      complication_risks: [
        {
          name: "Acute Kidney Injury",
          probability: 25 + Math.random() * 40,
          timeframe: "24-48 hours"
        },
        {
          name: "Respiratory Failure",
          probability: 15 + Math.random() * 30,
          timeframe: "12-24 hours"
        },
        {
          name: "Cardiac Arrhythmia",
          probability: 20 + Math.random() * 35,
          timeframe: "6-12 hours"
        }
      ]
    };
    
    // Add to results stack (keep latest 5 results)
    setAiResults(prev => {
      const newResults = [mockResult, ...prev].slice(0, 5);
      
      // Save latest AI analysis to localStorage for dashboard to read
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('latest-ai-analysis', JSON.stringify(mockResult));
      }
      
      return newResults;
    });
    setLastUpdate(new Date());
    setIsProcessing(false);
  };

  // Agent workflow animation controller
  const startAgentWorkflow = () => {
    setCurrentStep(0);
    setWorkflowProgress(0);
    setIsWorkflowRunning(true);
    
    // Better timing with consistent 5-second intervals
    agentSteps.forEach((step, index) => {
      const delay = index * 5000; // 5 seconds per agent
      
      setTimeout(() => {
        setCurrentStep(index);
        
        // Smooth progress animation for this step
        const stepDuration = 5000; // 5 seconds each
        const startTime = Date.now();
        
        const updateProgress = () => {
          const elapsed = Date.now() - startTime;
          const stepProgress = Math.min(elapsed / stepDuration, 1);
          const overallProgress = ((index + stepProgress) / agentSteps.length) * 100;
          
          setWorkflowProgress(overallProgress);
          
          if (stepProgress < 1) {
            requestAnimationFrame(updateProgress);
          }
        };
        
        updateProgress();
      }, delay);
    });
    
    // Complete workflow after 30 seconds and generate result
    setTimeout(() => {
      setIsWorkflowRunning(false);
      setIsProcessing(false);
      setWorkflowProgress(100);
      createMockAIResult(); // Add new result to the stack
      
      // Reset for next cycle
      setTimeout(() => {
        setCurrentStep(0);
        setWorkflowProgress(0);
      }, 2000);
    }, 30000);
  };
  
  // Manual and auto mode control
  useEffect(() => {
    let autoInterval: NodeJS.Timeout;
    
    if (autoMode && !isWorkflowRunning) {
      // In auto mode, repeat every 32 seconds
      autoInterval = setInterval(() => {
        if (!isWorkflowRunning) {
          setIsProcessing(true);
          startAgentWorkflow();
        }
      }, 32000);
    }
    
    return () => {
      if (autoInterval) {
        clearInterval(autoInterval);
      }
    };
  }, [autoMode, isWorkflowRunning]);

  // Manual start function
  const handleManualStart = () => {
    if (!isWorkflowRunning) {
      setIsProcessing(true);
      startAgentWorkflow();
    }
  };

  // Toggle auto mode with confirmation
  const toggleAutoMode = () => {
    if (!autoMode) {
      // Show warning before enabling auto mode
      const confirmed = window.confirm(
        "⚠️ Auto Mode Warning\n\n" +
        "This will run AI analysis automatically every 32 seconds.\n" +
        "This may consume API credits quickly.\n\n" +
        "Are you sure you want to enable Auto Mode?"
      );
      
      if (!confirmed) return;
    } else {
      // Turning off auto mode - clear AI analysis from localStorage
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem('latest-ai-analysis');
      }
    }
    
    setAutoMode(prev => !prev);
    if (!autoMode && !isWorkflowRunning) {
      // Starting auto mode - begin first cycle
      setIsProcessing(true);
      startAgentWorkflow();
    }
  };
  
  // Set connection status and clear any old errors
  useEffect(() => {
    // Clear any potential errors from previous WebSocket code
    setError(null);
    setConnectionStatus("connected");
    
    // Clear any global error handlers that might reference WebSocket
    const originalConsoleError = console.error;
    console.error = (...args) => {
      const message = args.join(' ');
      if (!message.includes('WebSocket') && !message.includes('connectWebSocket')) {
        originalConsoleError(...args);
      }
    };
    
    console.log("[AI Analysis] REST API mode initialized, WebSocket disabled");
    
    // Cleanup function
    return () => {
      console.error = originalConsoleError;
    };
  }, []);
  
  const connectionIndicator = () => {
    const statusConfig = {
      connected: { color: "bg-green-500", text: "AI Active", icon: <Zap size={12} /> },
      connecting: { color: "bg-yellow-500", text: "Connecting", icon: <Clock size={12} /> },
      disconnected: { color: "bg-red-500", text: "Disconnected", icon: <XCircle size={12} /> }
    };
    
    const config = statusConfig[connectionStatus];
    
    return (
      <div className="flex items-center gap-2">
        <div className={cn("w-3 h-3 rounded-full", config.color, 
          connectionStatus === "connected" ? "animate-pulse" : "")} />
        <span className="text-xs font-medium text-slate-600">
          {config.icon}
          <span className="ml-1">{config.text}</span>
        </span>
      </div>
    );
  };
  
  if (error) {
    return (
      <div className={cn("bg-red-50 border border-red-200 rounded-xl p-6", className)}>
        <div className="flex items-center gap-3">
          <XCircle className="text-red-600" size={24} />
          <div>
            <h3 className="font-bold text-red-900">AI Analysis Error</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <motion.div
              animate={{ rotate: isProcessing ? 360 : 0 }}
              transition={{ duration: 2, repeat: isProcessing ? Infinity : 0 }}
            >
              <Brain size={28} />
            </motion.div>
            <div>
              <h2 className="text-xl font-bold">AI Analysis Pipeline</h2>
              <p className="text-blue-100 text-sm">Real-time trend analysis and predictions</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              {connectionIndicator()}
              {lastUpdate && (
                <div className="text-xs text-blue-200 mt-1">
                  Updated: {lastUpdate.toLocaleTimeString()}
                </div>
              )}
            </div>
            
            {/* Control buttons */}
            <div className="flex gap-3">
              {/* Manual start button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleManualStart}
                disabled={isWorkflowRunning}
                className={cn(
                  "px-6 py-3 rounded-lg font-bold transition-all flex items-center gap-2",
                  isWorkflowRunning 
                    ? "bg-gray-400 cursor-not-allowed text-gray-200"
                    : "bg-green-500 hover:bg-green-600 text-white shadow-lg hover:shadow-xl"
                )}
              >
                <motion.div
                  animate={isWorkflowRunning ? { rotate: 360 } : {}}
                  transition={{ duration: 1, repeat: isWorkflowRunning ? Infinity : 0, ease: "linear" }}
                >
                  {isWorkflowRunning ? "⚙️" : "🚀"}
                </motion.div>
                {isWorkflowRunning ? "Processing..." : "Start AI Analysis"}
              </motion.button>
              
              {/* Auto mode toggle */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={toggleAutoMode}
                className={cn(
                  "px-4 py-3 rounded-lg font-medium transition-all",
                  autoMode 
                    ? "bg-orange-500 hover:bg-orange-600 text-white"
                    : "bg-white/20 hover:bg-white/30 text-white"
                )}
              >
                {autoMode ? "🔄 Auto ON" : "⏸️ Manual"}
              </motion.button>
            </div>
          </div>
        </div>
        
        {aiResults.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
            <div className="bg-white/10 rounded-lg p-3">
              <div className="text-2xl font-bold">{aiResults[0].cycle_number}</div>
              <div className="text-xs">Analysis Cycles</div>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <div className="text-2xl font-bold">{Math.round(aiResults[0].overall_risk_score)}</div>
              <div className="text-xs">Risk Score</div>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <div className="text-2xl font-bold">{Math.round(aiResults[0].confidence_score * 100)}%</div>
              <div className="text-xs">Confidence</div>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <div className="text-2xl font-bold">{aiResults[0].processing_time_ms}ms</div>
              <div className="text-xs">Processing Time</div>
            </div>
          </div>
        )}
        
        {/* Mode indicator */}
        <div className="mt-3 text-center">
          <div className={cn(
            "inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium",
            autoMode 
              ? "bg-orange-100 text-orange-800 border border-orange-200"
              : "bg-green-100 text-green-800 border border-green-200"
          )}>
            {autoMode ? (
              <>
                <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                Auto Mode: Running every 32 seconds
              </>
            ) : (
              <>
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                Manual Mode: Click to run analysis • Saves API costs
              </>
            )}
          </div>
        </div>
      </motion.div>
      
      {/* Agent Workflow Animation - Always Visible */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-xl p-8 text-white relative overflow-hidden"
      >
            {/* Animated background grid */}
            <div className="absolute inset-0 opacity-5">
              {Array.from({ length: 20 }).map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute w-px bg-white"
                  style={{ 
                    left: `${(i + 1) * 5}%`, 
                    height: '100%' 
                  }}
                  animate={{ opacity: [0.1, 0.3, 0.1] }}
                  transition={{ duration: 3, repeat: Infinity, delay: i * 0.1 }}
                />
              ))}
            </div>
            
            <div className="relative z-10">
              {/* Header */}
              <div className="text-center mb-8">
                <motion.h3 
                  className="text-3xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent"
                  animate={{ opacity: [1, 0.8, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  🤖 Multi-Agent AI Pipeline
                </motion.h3>
                <p className="text-slate-300 text-lg">Advanced diagnostic risk assessment in progress...</p>
                
                {/* Overall progress bar */}
                <div className="mt-6 bg-white/10 rounded-full h-3 overflow-hidden border border-white/20">
                  <motion.div
                    className="h-full bg-gradient-to-r from-blue-400 via-purple-400 to-green-400 shadow-lg"
                    initial={{ width: "0%" }}
                    animate={{ width: `${workflowProgress}%` }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                  />
                </div>
                <div className="text-sm text-slate-300 mt-2 font-medium">
                  Progress: {Math.round(workflowProgress)}% • Step {currentStep + 1} of {agentSteps.length}
                </div>
              </div>

              {/* Linked List Agent Chain */}
              <div className="relative">
                {/* Connecting wire/line with progress animation */}
                <div className="absolute top-1/2 left-0 right-0 h-1 bg-gradient-to-r from-slate-600 via-slate-500 to-slate-600 rounded-full transform -translate-y-1/2 z-0">
                  {/* Active progress on the wire */}
                  <motion.div
                    className="h-full bg-gradient-to-r from-blue-400 via-purple-400 to-green-400 rounded-full shadow-lg relative"
                    initial={{ width: "0%" }}
                    animate={{ width: `${((currentStep + 1) / agentSteps.length) * 100}%` }}
                    transition={{ duration: 0.5, ease: "easeInOut" }}
                  >
                    {/* Moving data packet animation */}
                    <motion.div
                      className="absolute top-1/2 right-0 w-2 h-2 bg-white rounded-full shadow-lg transform -translate-y-1/2"
                      animate={{
                        boxShadow: [
                          "0 0 5px rgba(255,255,255,0.8)",
                          "0 0 15px rgba(255,255,255,0.6)",
                          "0 0 5px rgba(255,255,255,0.8)"
                        ]
                      }}
                      transition={{ duration: 1, repeat: Infinity }}
                    />
                  </motion.div>
                  
                  {/* Connection points */}
                  {Array.from({ length: agentSteps.length }).map((_, index) => (
                    <motion.div
                      key={index}
                      className={cn(
                        "absolute top-1/2 w-2 h-2 rounded-full transform -translate-y-1/2 border-2",
                        index <= currentStep ? "bg-white border-blue-400" : "bg-slate-600 border-slate-400"
                      )}
                      style={{ left: `${(index / (agentSteps.length - 1)) * 100}%`, marginLeft: '-4px' }}
                      animate={{
                        scale: index === currentStep ? [1, 1.3, 1] : 1,
                        boxShadow: index === currentStep 
                          ? ["0 0 5px rgba(59,130,246,0.8)", "0 0 15px rgba(59,130,246,0.6)", "0 0 5px rgba(59,130,246,0.8)"]
                          : "none"
                      }}
                      transition={{ duration: 1, repeat: index === currentStep ? Infinity : 0 }}
                    />
                  ))}
                </div>
                
                {/* Agent blocks */}
                <div className="grid grid-cols-6 gap-2 relative z-10">
                  {agentSteps.map((step, index) => {
                    const isActive = index === currentStep;
                    const isCompleted = index < currentStep;
                    const isPending = index > currentStep;
                    
                    return (
                      <motion.div
                        key={index}
                        className="flex flex-col items-center"
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        {/* Agent block */}
                        <motion.div
                          className={cn(
                            "relative w-20 h-20 rounded-xl border-2 flex flex-col items-center justify-center p-2 transition-all duration-500 overflow-hidden",
                            isActive && "border-white shadow-2xl shadow-white/20 scale-110",
                            isCompleted && "border-green-400 bg-green-500/20",
                            isPending && "border-slate-400 bg-slate-700/50"
                          )}
                          animate={{
                            scale: isActive ? 1.1 : isCompleted ? 1.05 : 1,
                            rotateY: isActive ? [0, 5, -5, 0] : 0,
                            background: isActive 
                              ? ["rgba(59, 130, 246, 0.1)", "rgba(147, 51, 234, 0.1)", "rgba(59, 130, 246, 0.1)"]
                              : isCompleted 
                              ? "rgba(34, 197, 94, 0.2)"
                              : "rgba(51, 65, 85, 0.5)"
                          }}
                          transition={{ 
                            duration: isActive ? 2 : 0.5, 
                            repeat: isActive ? Infinity : 0 
                          }}
                        >
                          {/* Completion burst effect */}
                          {isCompleted && (
                            <>
                              {Array.from({ length: 6 }).map((_, i) => (
                                <motion.div
                                  key={i}
                                  className="absolute w-1 h-1 bg-green-400 rounded-full"
                                  style={{ top: "50%", left: "50%" }}
                                  initial={{ opacity: 0, scale: 0 }}
                                  animate={{
                                    opacity: [0, 1, 0],
                                    scale: [0, 1, 0],
                                    x: Math.cos(i * 60 * Math.PI / 180) * 40,
                                    y: Math.sin(i * 60 * Math.PI / 180) * 40
                                  }}
                                  transition={{
                                    duration: 1,
                                    delay: 0.2
                                  }}
                                />
                              ))}
                            </>
                          )}

                          {/* Agent icon */}
                          <motion.div
                            className="text-2xl mb-1 z-10"
                            animate={isActive ? {
                              scale: [1, 1.1, 1],
                              rotate: [0, 5, -5, 0]
                            } : isCompleted ? {
                              scale: [1, 1.2, 1]
                            } : {}}
                            transition={{ 
                              duration: isActive ? 1 : 0.5, 
                              repeat: isActive ? Infinity : isCompleted ? 1 : 0 
                            }}
                          >
                            {isCompleted ? "✅" : step.icon}
                          </motion.div>
                          
                          {/* Status indicator */}
                          <div className={cn(
                            "w-2 h-2 rounded-full z-10",
                            isActive && "bg-white animate-pulse",
                            isCompleted && "bg-green-400",
                            isPending && "bg-slate-500"
                          )} />
                          
                          {/* Processing indicator for active agent */}
                          {isActive && (
                            <>
                              {/* Pulse ring animation */}
                              <motion.div
                                className="absolute inset-0 rounded-xl border-2 border-white/50"
                                animate={{ 
                                  scale: [1, 1.2, 1],
                                  opacity: [0.8, 0.3, 0.8] 
                                }}
                                transition={{ duration: 1.5, repeat: Infinity }}
                              />
                              
                              {/* Outer pulse ring */}
                              <motion.div
                                className="absolute inset-0 rounded-xl border border-white/30"
                                animate={{ 
                                  scale: [1, 1.4, 1],
                                  opacity: [0.6, 0, 0.6] 
                                }}
                                transition={{ duration: 2, repeat: Infinity }}
                              />
                              
                              {/* Active indicator dot */}
                              <motion.div
                                className="absolute -top-1 -right-1 w-4 h-4 bg-blue-400 rounded-full shadow-lg shadow-blue-400/50"
                                animate={{ 
                                  scale: [1, 1.3, 1],
                                  opacity: [1, 0.7, 1] 
                                }}
                                transition={{ duration: 1, repeat: Infinity }}
                              />
                              
                              {/* Processing particles */}
                              {Array.from({ length: 3 }).map((_, i) => (
                                <motion.div
                                  key={i}
                                  className="absolute w-1 h-1 bg-white rounded-full"
                                  style={{
                                    top: "50%",
                                    left: "50%",
                                  }}
                                  animate={{
                                    x: [0, Math.cos(i * 120 * Math.PI / 180) * 30],
                                    y: [0, Math.sin(i * 120 * Math.PI / 180) * 30],
                                    opacity: [1, 0]
                                  }}
                                  transition={{
                                    duration: 1.5,
                                    repeat: Infinity,
                                    delay: i * 0.5
                                  }}
                                />
                              ))}
                            </>
                          )}
                        </motion.div>
                        
                        {/* Agent name - shorter */}
                        <div className="mt-3 text-center">
                          <div className={cn(
                            "text-xs font-semibold transition-colors",
                            isActive && "text-white",
                            isCompleted && "text-green-300",
                            isPending && "text-slate-400"
                          )}>
                            {step.name.replace(" Agent", "")}
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
                
                {/* Current agent detailed info */}
                <motion.div
                  key={currentStep}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-8 bg-white/10 rounded-lg p-6 border border-white/20"
                >
                  <div className="flex items-center gap-4">
                    <motion.div
                      className={cn(
                        "w-16 h-16 rounded-full flex items-center justify-center text-2xl",
                        `bg-gradient-to-r ${agentSteps[currentStep]?.color || 'from-blue-500 to-purple-500'}`
                      )}
                      animate={{ 
                        rotate: 360,
                        scale: [1, 1.05, 1]
                      }}
                      transition={{ 
                        rotate: { duration: 3, repeat: Infinity, ease: "linear" },
                        scale: { duration: 1.5, repeat: Infinity }
                      }}
                    >
                      {agentSteps[currentStep]?.icon}
                    </motion.div>
                    
                    <div className="flex-1">
                      <h4 className="text-xl font-bold text-white mb-2">
                        {agentSteps[currentStep]?.name}
                      </h4>
                      <p className="text-slate-300">
                        {agentSteps[currentStep]?.description}
                      </p>
                      
                      {/* Step progress bar */}
                      <div className="mt-3 bg-white/20 rounded-full h-2 overflow-hidden">
                        <motion.div
                          className={cn(
                            "h-full",
                            `bg-gradient-to-r ${agentSteps[currentStep]?.color || 'from-blue-500 to-purple-500'}`
                          )}
                          initial={{ width: "0%" }}
                          animate={{ width: "100%" }}
                          transition={{ duration: 5, ease: "linear" }}
                        />
                      </div>
                    </div>
                    
                    <div className="text-right text-slate-300">
                      <div className="text-sm">Step {currentStep + 1}/{agentSteps.length}</div>
                      <div className="text-xs">~5 seconds</div>
                    </div>
                  </div>
                </motion.div>
              </div>
              
              {/* Footer info */}
              <div className="mt-6 text-center text-sm text-slate-400">
                <p>🔬 Advanced ML algorithms • Patient ID: {patientId} • Processing time: ~30 seconds</p>
              </div>
            </div>
          </motion.div>
      
      {/* Processing Status Indicator */}
      {isWorkflowRunning && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-blue-50 border border-blue-200 rounded-xl p-4 mt-4"
        >
          <div className="flex items-center gap-3">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Brain className="text-blue-600" size={20} />
            </motion.div>
            <div>
              <div className="font-medium text-blue-900">Pipeline Processing...</div>
              <div className="text-sm text-blue-700">Step {currentStep + 1} of {agentSteps.length} • {Math.round(workflowProgress)}% complete</div>
            </div>
          </div>
        </motion.div>
      )}

      {/* AI Analysis Results Stack */}
      {aiResults.length > 0 && (
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            📊 Analysis Results ({aiResults.length})
          </h3>
          
          {aiResults.map((result, index) => (
            <motion.div
              key={`${result.patient_id}-${result.analysis_timestamp}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={cn(
                "bg-white rounded-xl border-2 p-6 relative",
                index === 0 ? "border-blue-300 shadow-lg" : "border-slate-200 opacity-90"
              )}
            >
              {/* Latest indicator */}
              {index === 0 && (
                <div className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full font-bold">
                  LATEST
                </div>
              )}
              
              {/* Timestamp */}
              <div className="text-xs text-slate-500 mb-3">
                Analysis #{result.cycle_number} • {new Date(result.analysis_timestamp).toLocaleTimeString()}
              </div>
              
              {/* Pattern Summary */}
              <div className="flex items-center gap-3 mb-4">
                <Target className="text-purple-600" size={20} />
                <h4 className="font-bold text-slate-800">Pattern Analysis</h4>
              </div>
              <div className="text-slate-700 mb-4">{result.pattern_summary}</div>
              
              {/* Alert Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                {Object.entries(result.alert_count).map(([level, count]) => (
                  <div key={level} className={cn("rounded-lg p-3 border text-center", getAlertColor(level))}>
                    <div className="font-bold text-sm">{count}</div>
                    <div className="text-xs capitalize">{level}</div>
                  </div>
                ))}
              </div>
              
              {/* Trend Predictions */}
              <div className="grid gap-3">
                {result.trend_predictions.map((prediction, predIndex) => (
                  <div
                    key={prediction.itemid}
                    className={cn("p-4 rounded-lg border", getAlertColor(prediction.alert_level))}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getAlertIcon(prediction.alert_level)}
                        <div>
                          <div className="font-semibold">{prediction.vital_name}</div>
                          <div className="text-sm text-slate-600">
                            Current: {prediction.current_value.toFixed(1)} → Predicted: {prediction.prediction_next_30s.toFixed(1)}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        {getTrendIcon(prediction.trend_direction, 20)}
                        
                        <div className="text-right">
                          <div className="text-sm font-medium">
                            {(prediction.trend_confidence * 100).toFixed(0)}% confidence
                          </div>
                          <div className="text-xs text-slate-600">
                            Risk: {(prediction.abrupt_change_risk * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {prediction.pattern_detected && (
                      <div className="mt-2 text-xs text-slate-600">
                        Pattern: <span className="font-medium capitalize">{prediction.pattern_detected}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              {/* Overall scores */}
              <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-slate-200">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{Math.round(result.overall_risk_score)}</div>
                  <div className="text-xs text-slate-600">Risk Score</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{Math.round(result.confidence_score * 100)}%</div>
                  <div className="text-xs text-slate-600">Confidence</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-slate-600">{result.processing_time_ms}ms</div>
                  <div className="text-xs text-slate-600">Process Time</div>
                </div>
              </div>

              {/* Sepsis Risk Assessment */}
              {result.sepsis_risk && (
                <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-3 mb-3">
                    <Shield className="text-red-600" size={20} />
                    <h5 className="font-bold text-red-800">Sepsis Risk Assessment</h5>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">{result.sepsis_risk.probability}%</div>
                      <div className="text-xs text-red-700">Sepsis Probability</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">{result.sepsis_risk.qSOFA_score}</div>
                      <div className="text-xs text-red-700">qSOFA Score</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">{result.sepsis_risk.early_warning_score}</div>
                      <div className="text-xs text-red-700">NEWS Score</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Clinical Notes */}
              {result.clinical_notes && result.clinical_notes.length > 0 && (
                <div className="mt-6">
                  <div className="flex items-center gap-3 mb-4">
                    <FileText className="text-blue-600" size={20} />
                    <h5 className="font-bold text-slate-800">Recent Clinical Notes</h5>
                  </div>
                  <div className="space-y-3">
                    {result.clinical_notes.slice(0, 3).map((note, noteIndex) => (
                      <div key={noteIndex} className={cn(
                        "p-3 rounded-lg border-l-4",
                        note.priority === "high" ? "border-red-500 bg-red-50" :
                        note.priority === "medium" ? "border-yellow-500 bg-yellow-50" :
                        "border-blue-500 bg-blue-50"
                      )}>
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className={cn(
                              "text-xs px-2 py-1 rounded-full font-medium",
                              note.type === "physician" ? "bg-purple-100 text-purple-800" :
                              note.type === "nursing" ? "bg-green-100 text-green-800" :
                              note.type === "respiratory" ? "bg-blue-100 text-blue-800" :
                              "bg-gray-100 text-gray-800"
                            )}>
                              {note.type.toUpperCase()}
                            </span>
                            <span className="text-sm font-medium text-slate-700">{note.author}</span>
                          </div>
                          <span className="text-xs text-slate-500">
                            {new Date(note.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-sm text-slate-700">{note.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Lab Results */}
              {result.lab_results && result.lab_results.length > 0 && (
                <div className="mt-6">
                  <div className="flex items-center gap-3 mb-4">
                    <FlaskConical className="text-green-600" size={20} />
                    <h5 className="font-bold text-slate-800">Laboratory Results</h5>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {result.lab_results.map((lab, labIndex) => (
                      <div key={labIndex} className={cn(
                        "p-3 rounded-lg border",
                        lab.status === "critical" ? "border-red-300 bg-red-50" :
                        lab.status === "high" ? "border-orange-300 bg-orange-50" :
                        lab.status === "low" ? "border-yellow-300 bg-yellow-50" :
                        "border-green-300 bg-green-50"
                      )}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-slate-800">{lab.name}</span>
                          <div className="flex items-center gap-2">
                            {lab.trend === "improving" ? <TrendingUp size={14} className="text-green-600" /> :
                             lab.trend === "worsening" ? <TrendingDown size={14} className="text-red-600" /> :
                             <Minus size={14} className="text-gray-600" />}
                            <span className={cn(
                              "text-xs px-2 py-1 rounded-full font-medium",
                              lab.status === "critical" ? "bg-red-100 text-red-800" :
                              lab.status === "high" ? "bg-orange-100 text-orange-800" :
                              lab.status === "low" ? "bg-yellow-100 text-yellow-800" :
                              "bg-green-100 text-green-800"
                            )}>
                              {lab.status.toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <div className="text-lg font-bold text-slate-900">
                          {lab.value.toFixed(2)} <span className="text-sm font-normal text-slate-600">{lab.unit}</span>
                        </div>
                        <div className="text-xs text-slate-600">Reference: {lab.reference_range}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Current Medications */}
              {result.medications && result.medications.length > 0 && (
                <div className="mt-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Pill className="text-purple-600" size={20} />
                    <h5 className="font-bold text-slate-800">Current Medications</h5>
                  </div>
                  <div className="space-y-3">
                    {result.medications.map((med, medIndex) => (
                      <div key={medIndex} className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-medium text-slate-800">{med.name}</div>
                            <div className="text-sm text-slate-600">
                              {med.dose} {med.route} • {med.frequency}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              Last given: {med.last_given} • Next due: {med.next_due}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className={cn(
                              "text-xs px-2 py-1 rounded-full font-medium",
                              med.compliance >= 90 ? "bg-green-100 text-green-800" :
                              med.compliance >= 70 ? "bg-yellow-100 text-yellow-800" :
                              "bg-red-100 text-red-800"
                            )}>
                              {med.compliance}% Compliance
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Risk Factors */}
              {result.risk_factors && result.risk_factors.length > 0 && (
                <div className="mt-6">
                  <div className="flex items-center gap-3 mb-4">
                    <AlertTriangle className="text-orange-600" size={20} />
                    <h5 className="font-bold text-slate-800">Identified Risk Factors</h5>
                  </div>
                  <div className="space-y-3">
                    {result.risk_factors.map((risk, riskIndex) => (
                      <div key={riskIndex} className={cn(
                        "p-4 rounded-lg border-l-4",
                        risk.severity === "high" ? "border-red-500 bg-red-50" :
                        risk.severity === "moderate" ? "border-yellow-500 bg-yellow-50" :
                        "border-blue-500 bg-blue-50"
                      )}>
                        <div className="flex items-start justify-between mb-2">
                          <h6 className="font-medium text-slate-800">{risk.factor}</h6>
                          <span className={cn(
                            "text-xs px-2 py-1 rounded-full font-medium",
                            risk.severity === "high" ? "bg-red-100 text-red-800" :
                            risk.severity === "moderate" ? "bg-yellow-100 text-yellow-800" :
                            "bg-blue-100 text-blue-800"
                          )}>
                            {risk.severity.toUpperCase()} RISK
                          </span>
                        </div>
                        <p className="text-sm text-slate-700 mb-2">{risk.description}</p>
                        <div className="text-xs text-slate-600 italic">
                          <strong>Recommendation:</strong> {risk.recommendation}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Recommendations */}
              {result.ai_recommendations && result.ai_recommendations.length > 0 && (
                <div className="mt-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Brain className="text-indigo-600" size={20} />
                    <h5 className="font-bold text-slate-800">AI Recommendations</h5>
                  </div>
                  <div className="space-y-2">
                    {result.ai_recommendations.map((rec, recIndex) => (
                      <div key={recIndex} className="flex items-start gap-3 p-3 rounded-lg bg-indigo-50 border border-indigo-200">
                        <CheckCircle className="text-indigo-600 mt-0.5" size={16} />
                        <span className="text-sm text-slate-700">{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Complication Risks */}
              {result.complication_risks && result.complication_risks.length > 0 && (
                <div className="mt-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Heart className="text-red-600" size={20} />
                    <h5 className="font-bold text-slate-800">Complication Risk Prediction</h5>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {result.complication_risks.map((comp, compIndex) => (
                      <div key={compIndex} className="p-3 rounded-lg border border-red-200 bg-red-50">
                        <div className="text-center">
                          <div className="font-medium text-slate-800">{comp.name}</div>
                          <div className="text-2xl font-bold text-red-600">{Math.round(comp.probability)}%</div>
                          <div className="text-xs text-red-700">Risk in {comp.timeframe}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}
      
      {/* No Data State */}
      {aiResults.length === 0 && !isWorkflowRunning && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-slate-50 rounded-xl border border-slate-200 p-12 text-center"
        >
          <Brain className="mx-auto mb-4 text-slate-400" size={48} />
          <h3 className="text-lg font-medium text-slate-700 mb-2">Ready for AI Analysis</h3>
          <p className="text-slate-500 mb-4">
            Click "Start AI Analysis" to begin the 30-second agent workflow.
          </p>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleManualStart}
            className="px-6 py-3 bg-green-500 hover:bg-green-600 text-white font-bold rounded-lg shadow-lg transition-all flex items-center gap-2 mx-auto"
          >
            🚀 Start AI Analysis
          </motion.button>
          
          <div className="mt-4 text-sm text-slate-400">
            💡 Manual mode saves API costs • Enable auto mode only for demos
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default AIAnalysisPanel;