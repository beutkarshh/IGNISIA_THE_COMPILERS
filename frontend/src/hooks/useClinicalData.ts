"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

export interface PatientRecord {
  subject_id: number;
  gender: string;
  dob: string;
  admission_type?: string;
  diagnosis?: string;
}

export function useClinicalData() {
  const [patients, setPatients] = useState<PatientRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchPatients() {
      try {
        // Fetch top 5 patients and join with their latest admission for context
        const { data, error } = await supabase
          .from("patients")
          .select(`
            subject_id,
            gender,
            dob,
            admissions (
              admission_type,
              diagnosis
            )
          `)
          .limit(6);

        if (error) throw error;

        const formatted = data.map((p: any) => ({
          subject_id: p.subject_id,
          gender: p.gender,
          dob: p.dob,
          admission_type: p.admissions?.[0]?.admission_type || "N/A",
          diagnosis: p.admissions?.[0]?.diagnosis || "No Current Diagnosis"
        }));

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
