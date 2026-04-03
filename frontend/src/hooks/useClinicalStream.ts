"use client";

import { useEffect, useState, useRef } from "react";
import { supabase } from "@/lib/supabase";

export interface VitalRecord {
  subject_id: number;
  itemid: number;
  valuenum: number;
  valueuom: string;
  charttime: string;
  is_outlier: boolean;
}

export function useClinicalStream(subjectIds: number[]) {
  const [vitals, setVitals] = useState<Record<number, VitalRecord[]>>({});
  const vitalsRef = useRef<Record<number, VitalRecord[]>>({});

  useEffect(() => {
    // 1. Initial State for each patient
    const initial: Record<number, VitalRecord[]> = {};
    subjectIds.forEach((id) => (initial[id] = []));
    setVitals(initial);
    vitalsRef.current = initial;

    // 2. Real-time Subscription to THE PULSE
    const channel = supabase
      .channel("live_telemetry_stream")
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "live_telemetry",
        },
        (payload) => {
          const newRecord = payload.new as VitalRecord;
          const sid = newRecord.subject_id;

          if (subjectIds.includes(sid)) {
            // Update Ref (Immediate)
            const current = [...(vitalsRef.current[sid] || [])];
            current.push(newRecord);
            
            // Keep only the last 50 points for the trend chart
            if (current.length > 50) current.shift();
            vitalsRef.current[sid] = current;
          }
        }
      )
      .subscribe();

    // 3. UI Sync - Throttle state updates to 100ms to match ingestion
    const syncInterval = setInterval(() => {
      setVitals({ ...vitalsRef.current });
    }, 100);

    return () => {
      supabase.removeChannel(channel);
      clearInterval(syncInterval);
    };
  }, [subjectIds.join(",")]);

  return { vitals };
}
