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

        const criticalTerms = ["SEPSIS", "PNEUMONIA", "FEVER", "HYPOTENSION", "FAILURE", "DISTRESS", "ARREST", "BRADYCARDIA"];

        const formatted = data.map((p: any) => {
          const mainDiagnosis = p.admissions?.[0]?.diagnosis || "Clinical Evaluation";
          const isCriticalDx = criticalTerms.some(term => mainDiagnosis.toUpperCase().includes(term));
          const hasAbnormalLabs = (abnormalCounts[p.subject_id] || 0) > 50;

          return {
            subject_id: p.subject_id,
            gender: p.gender,
            dob: new Date(p.dob).toLocaleDateString(),
            admission_type: p.admissions?.[0]?.admission_type || "N/A",
            diagnosis: mainDiagnosis,
            insurance: p.admissions?.[0]?.insurance,
            language: p.admissions?.[0]?.language,
            is_alert: isCriticalDx || hasAbnormalLabs,
            bpm: 60 + Math.floor(Math.random() * 40) + (isCriticalDx ? 30 : 0) // Simulated current BPM for registry, will be updated by telemetry
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
