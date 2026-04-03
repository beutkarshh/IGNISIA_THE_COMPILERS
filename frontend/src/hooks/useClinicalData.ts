"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

export interface PatientRecord {
  subject_id: number;
  gender: string;
  dob: string;
  admission_type?: string;
  diagnosis?: string;
  insurance?: string;
  language?: string;
  is_alert: boolean;
  bpm: number;
}

export function useClinicalData() {
  const [patients, setPatients] = useState<PatientRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchPatients() {
      try {
        // Fetch all patients and join with their latest admission for context
        const { data, error } = await supabase
          .from("patients")
          .select(`
            subject_id,
            gender,
            dob,
            admissions (
              admittime,
              admission_type,
              diagnosis,
              insurance,
              language
            )
          `)
          .order("subject_id", { ascending: true });

        if (error) throw error;

        // Fetch abnormal count for each patient to determine stability
        const { data: abnormalLabs } = await supabase
          .from("labevents")
          .select("subject_id")
          .eq("flag", "abnormal");

        const abnormalCounts = abnormalLabs?.reduce((acc: Record<number, number>, curr) => {
          acc[curr.subject_id] = (acc[curr.subject_id] || 0) + 1;
          return acc;
        }, {}) || {};

        const criticalTerms = [
          "SEPSIS","SEPTIC","PNEUMONIA","FEVER","HYPOTENSION","FAILURE",
          "DISTRESS","ARREST","BRADYCARDIA","HEMORRHAGE","STROKE","CVA",
          "ARDS","SHOCK","RESPIRATORY FAILURE","CARDIAC","INFARCTION",
          "INTRACRANIAL","COMA","TRAUMA","SEPTICEMIA",
        ];

        const formatted = data.map((p: any) => {
          // Pick the most-recent admission's diagnosis
          const admissions: any[] = p.admissions || [];
          // Sort by admittime descending if available, otherwise take last element
          const sorted = [...admissions].sort((a, b) => {
            if (a.admittime && b.admittime) return new Date(b.admittime).getTime() - new Date(a.admittime).getTime();
            return 0;
          });
          const latestAdmission = sorted[0] || {};
          const mainDiagnosis = (latestAdmission.diagnosis || "Clinical Evaluation").toUpperCase();
          const isCriticalDx = criticalTerms.some(term => mainDiagnosis.includes(term));
          const hasAbnormalLabs = (abnormalCounts[p.subject_id] || 0) > 50;

          return {
            subject_id: p.subject_id,
            gender: p.gender,
            dob: new Date(p.dob).toLocaleDateString(),
            admission_type: latestAdmission.admission_type || "N/A",
            diagnosis: mainDiagnosis,   // already uppercased — consistent with keyword matching
            insurance: latestAdmission.insurance,
            language: latestAdmission.language,
            is_alert: isCriticalDx || hasAbnormalLabs,
            bpm: 60 + Math.floor(Math.random() * 40) + (isCriticalDx ? 30 : 0)
          };
        });

        setPatients(formatted);
      } catch (e) {
        console.error("Failed to fetch relational clinical data:", e);
      } finally {
        setIsLoading(false);
      }
    }

    fetchPatients();
  }, []);

  return { patients, isLoading };
}
