"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Clock, FileText, Activity, TrendingUp, TrendingDown, 
  AlertTriangle, User, Calendar, Stethoscope, FlaskConical,
  Heart, Thermometer, Droplets, Wind, Gauge, Printer,
  ChevronDown, ChevronUp
} from "lucide-react";
import { cn } from "@/lib/utils";
import { VitalTrend } from "./VitalTrend";
import { PatientRecord } from "@/hooks/useClinicalData";

interface VitalSigns {
  heart_rate?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  respiratory_rate?: number;
  temperature?: number;
  spo2?: number;
}

interface LabValues {
  wbc?: number;
  lactate?: number;
  creatinine?: number;
  bun?: number;
  platelets?: number;
}

interface TimelinePoint {
  timestamp: string;
  time_label: string;
  hours_since_admission: number;
  vitals: VitalSigns;
  labs: LabValues;
  notes: string;
}

interface Assessment {
  id: string;
  patient_id: string;
  sepsis_risk_score: number;
  clinical_flags: string[];
  summary: string;
  timestamp: string;
}

interface ShiftHandoverData {
  patient: PatientRecord;
  timeline: TimelinePoint[];
  current_assessment?: Assessment;
  vital_trends: any[];
}

interface ShiftHandoverReportProps {
  patient: PatientRecord;
  vitals?: any[];
  className?: string;
  onPrintReport?: () => void;
}

export function ShiftHandoverReport({ 
  patient, 
  vitals = [], 
  className,
  onPrintReport 
}: ShiftHandoverReportProps) {
  const [handoverData, setHandoverData] = useState<ShiftHandoverData | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    demographics: true,
    vitals: true,
    assessment: true,
    timeline: true,
    recommendations: false
  });

  // Calculate key metrics
  const admissionDate = new Date(); // Default to today since admission_time not available
  const currentDate = new Date();
  const daysSinceAdmission = 1; // Default placeholder
  
  // Calculate age from DOB
  const calculateAge = (dob: string) => {
    try {
      const birthDate = new Date(dob);
      const today = new Date();
      let age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }
      return age;
    } catch {
      return "Unknown";
    }
  };

  const patientAge = calculateAge(patient.dob);
  
  // Get latest vitals for current status
  const currentVitals = vitals.length > 0 ? vitals[vitals.length - 1] : null;

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const generateShiftSummary = () => {
    const admissionLength = daysSinceAdmission;
    const diagnosis = patient.diagnosis || "Intensive care monitoring";
    
    return `${patientAge}-year-old ${patient.gender.toLowerCase()} patient in ICU for ${diagnosis}. Currently under active monitoring with vital signs tracking. Review clinical status and continue monitoring protocols.`;
  };

  const getCriticalAlerts = () => {
    const alerts = [];
    
    if (currentVitals) {
      if (currentVitals.valuenum > 100 && vitals.some(v => [211, 220045].includes(v.itemid))) {
        alerts.push({ type: "warning", message: "Tachycardia - HR > 100 BPM" });
      }
      if (currentVitals.valuenum < 60 && vitals.some(v => [211, 220045].includes(v.itemid))) {
        alerts.push({ type: "warning", message: "Bradycardia - HR < 60 BPM" });
      }
    }
    
    return alerts;
  };

  const HandoverSection = ({ 
    title, 
    icon: Icon, 
    sectionKey, 
    children, 
    critical = false 
  }: { 
    title: string; 
    icon: any; 
    sectionKey: keyof typeof expandedSections; 
    children: React.ReactNode;
    critical?: boolean;
  }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        "border rounded-xl bg-white/50 backdrop-blur-sm",
        critical ? "border-orange-200 bg-orange-50/50" : "border-slate-200"
      )}
    >
      <button
        onClick={() => toggleSection(sectionKey)}
        className={cn(
          "w-full px-6 py-4 flex items-center justify-between text-left hover:bg-slate-50/50 transition-colors rounded-t-xl",
          critical && "hover:bg-orange-50/70"
        )}
      >
        <div className="flex items-center gap-3">
          <Icon size={20} className={cn("text-slate-600", critical && "text-orange-600")} />
          <h3 className={cn(
            "text-lg font-bold",
            critical ? "text-orange-900" : "text-slate-900"
          )}>
            {title}
          </h3>
        </div>
        {expandedSections[sectionKey] ? (
          <ChevronUp size={20} className="text-slate-400" />
        ) : (
          <ChevronDown size={20} className="text-slate-400" />
        )}
      </button>
      
      {expandedSections[sectionKey] && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="px-6 pb-6"
        >
          {children}
        </motion.div>
      )}
    </motion.div>
  );

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
            <FileText className="text-blue-600" />
            Shift Handover Report
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            Patient ID: {patient.subject_id} • Generated: {new Date().toLocaleString()}
          </p>
        </div>
        <button
          onClick={onPrintReport}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Printer size={16} />
          Print Report
        </button>
      </div>

      {/* Critical Alerts Banner */}
      {getCriticalAlerts().length > 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-xl p-4"
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-orange-600" size={24} />
            <div>
              <h3 className="font-bold text-orange-900">Critical Alerts</h3>
              <div className="space-y-1 mt-2">
                {getCriticalAlerts().map((alert, idx) => (
                  <p key={idx} className="text-orange-800 text-sm">• {alert.message}</p>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Demographics & Admission */}
      <HandoverSection
        title="Patient Demographics & Admission"
        icon={User}
        sectionKey="demographics"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <User size={16} className="text-slate-500" />
              <span className="font-medium">Demographics:</span>
              <span>{patientAge}-year-old {patient.gender.toLowerCase()}</span>
            </div>
            <div className="flex items-center gap-3">
              <Calendar size={16} className="text-slate-500" />
              <span className="font-medium">DOB:</span>
              <span>{new Date(patient.dob).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center gap-3">
              <Stethoscope size={16} className="text-slate-500" />
              <span className="font-medium">Type:</span>
              <span className="capitalize">{patient.admission_type?.toLowerCase() || "Standard"}</span>
            </div>
          </div>
          <div className="space-y-3">
            <div>
              <span className="font-medium text-slate-700">Primary Diagnosis:</span>
              <p className="text-slate-900 mt-1 p-3 bg-blue-50 rounded-lg">
                {patient.diagnosis || "ICU monitoring"}
              </p>
            </div>
            <div className="text-sm text-slate-600">
              <span className="font-medium">Insurance:</span> {patient.insurance || "Not specified"}
            </div>
          </div>
        </div>
      </HandoverSection>

      {/* Shift Summary */}
      <HandoverSection
        title="Shift Summary"
        icon={Clock}
        sectionKey="recommendations"
      >
        <div className="bg-slate-50 rounded-lg p-4">
          <p className="text-slate-800 leading-relaxed">
            {generateShiftSummary()}
          </p>
        </div>
        
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{daysSinceAdmission}</div>
            <div className="text-sm text-blue-800">Days in ICU</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{vitals.length}</div>
            <div className="text-sm text-green-800">Vital Records</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {patient.admission_type?.charAt(0).toUpperCase() || "S"}
            </div>
            <div className="text-sm text-purple-800">Admission Type</div>
          </div>
        </div>
      </HandoverSection>

      {/* Vital Signs Trends */}
      <HandoverSection
        title="Vital Signs Overview (Last 24 Hours)"
        icon={Activity}
        sectionKey="vitals"
      >
        {vitals.length > 0 ? (
          <div className="space-y-6">
            {/* Current vital signs cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-red-50 rounded-lg p-4 text-center">
                <Heart className="mx-auto mb-2 text-red-600" size={24} />
                <div className="text-2xl font-bold text-red-900">
                  {currentVitals?.valuenum || "--"}
                </div>
                <div className="text-xs text-red-700">Heart Rate (BPM)</div>
              </div>
              
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <Gauge className="mx-auto mb-2 text-blue-600" size={24} />
                <div className="text-2xl font-bold text-blue-900">--/--</div>
                <div className="text-xs text-blue-700">Blood Pressure</div>
              </div>
              
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <Droplets className="mx-auto mb-2 text-green-600" size={24} />
                <div className="text-2xl font-bold text-green-900">--</div>
                <div className="text-xs text-green-700">SpO2 (%)</div>
              </div>
              
              <div className="bg-orange-50 rounded-lg p-4 text-center">
                <Wind className="mx-auto mb-2 text-orange-600" size={24} />
                <div className="text-2xl font-bold text-orange-900">--</div>
                <div className="text-xs text-orange-700">Resp Rate</div>
              </div>
              
              <div className="bg-purple-50 rounded-lg p-4 text-center">
                <Thermometer className="mx-auto mb-2 text-purple-600" size={24} />
                <div className="text-2xl font-bold text-purple-900">--</div>
                <div className="text-xs text-purple-700">Temperature</div>
              </div>
            </div>

            {/* Trend charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <VitalTrend 
                label="Heart Rate Trend" 
                unit="BPM" 
                color="#DC2626" 
                data={vitals.filter(v => [211, 220045].includes(v.itemid))} 
                yMin={50} 
                yMax={150}
              />
              <VitalTrend 
                label="Blood Pressure Trend" 
                unit="mmHg" 
                color="#2563EB" 
                data={vitals.filter(v => [456, 52, 6702, 443, 220052, 220181, 225312].includes(v.itemid))} 
                yMin={60} 
                yMax={180}
              />
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500">
            <Activity className="mx-auto mb-2" size={48} />
            <p>No recent vital signs data available</p>
          </div>
        )}
      </HandoverSection>

      {/* Laboratory Values */}
      <HandoverSection
        title="Laboratory Values"
        icon={FlaskConical}
        sectionKey="timeline"
      >
        <div className="bg-amber-50 rounded-lg p-4 text-center">
          <FlaskConical className="mx-auto mb-2 text-amber-600" size={48} />
          <p className="text-amber-800">Laboratory data integration coming soon</p>
          <p className="text-sm text-amber-700 mt-1">
            Will include: CBC, BMP, ABG, Lactate, Liver function, Coagulation studies
          </p>
        </div>
      </HandoverSection>

      {/* Handover Notes */}
      <HandoverSection
        title="Handover Notes & Action Items"
        icon={FileText}
        sectionKey="assessment"
        critical
      >
        <div className="space-y-4">
          <div className="bg-orange-50 rounded-lg p-4">
            <h4 className="font-bold text-orange-900 mb-2">For Incoming Physician:</h4>
            <ul className="space-y-2 text-orange-800">
              <li>• Monitor vital signs trends - patient in ICU for {patient.diagnosis || "monitoring"}</li>
              <li>• Continue current treatment protocols</li>
              <li>• Watch for any changes in neurological status</li>
              <li>• Review lab results when available</li>
              <li>• Consider family communication needs</li>
            </ul>
          </div>
          
          <div className="bg-yellow-50 rounded-lg p-4">
            <h4 className="font-bold text-yellow-900 mb-2">Outstanding Items:</h4>
            <ul className="space-y-1 text-yellow-800">
              <li>• Nursing notes integration pending</li>
              <li>• Medication reconciliation review needed</li>
              <li>• Assessment history compilation in progress</li>
            </ul>
          </div>
        </div>
      </HandoverSection>

      {/* Footer */}
      <div className="border-t pt-4 text-center text-sm text-slate-500">
        Generated by IGNISIA ICU Clinical Assistant • {new Date().toLocaleString()}
      </div>
    </div>
  );
}

export default ShiftHandoverReport;