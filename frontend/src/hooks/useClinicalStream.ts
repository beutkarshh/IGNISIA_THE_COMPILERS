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

// AI Pipeline Integration
let aiDataBuffer: Record<number, VitalRecord[]> = {};
let aiBufferCounts: Record<number, number> = {};
const AI_BUFFER_SIZE = 3; // Process every 3 data points

const sendToAIPipeline = async (record: VitalRecord) => {
  const patientId = record.subject_id;
  
  // Initialize buffer for patient if needed
  if (!aiDataBuffer[patientId]) {
    aiDataBuffer[patientId] = [];
    aiBufferCounts[patientId] = 0;
  }
  
  // Add to buffer
  aiDataBuffer[patientId].push(record);
  aiBufferCounts[patientId]++;
  
  // Process if we have enough data points
  if (aiBufferCounts[patientId] >= AI_BUFFER_SIZE) {
    try {
      const telemetryBatch = [...aiDataBuffer[patientId]];
      
      // Send to AI service
      const response = await fetch(`/api/ai/process-telemetry/${patientId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(telemetryBatch)
      });
      
      if (response.ok) {
        console.log(`[AI Pipeline] Processed ${telemetryBatch.length} data points for patient ${patientId}`);
      } else {
        console.warn(`[AI Pipeline] Failed to process data for patient ${patientId}`);
      }
      
      // Reset buffer
      aiDataBuffer[patientId] = [];
      aiBufferCounts[patientId] = 0;
      
    } catch (error) {
      console.error('[AI Pipeline] Error sending telemetry data:', error);
      // Reset buffer on error to prevent infinite accumulation
      aiDataBuffer[patientId] = [];
      aiBufferCounts[patientId] = 0;
    }
  }
};

export function useClinicalStream(subjectIds: number[]) {
  const [vitals, setVitals] = useState<Record<number, VitalRecord[]>>({});
  const vitalsRef = useRef<Record<number, VitalRecord[]>>({});

  useEffect(() => {
    if (subjectIds.length === 0) return;

    // 1. Initialise empty state
    const initial: Record<number, VitalRecord[]> = {};
    subjectIds.forEach((id) => (initial[id] = []));
    vitalsRef.current = initial;
    setVitals({ ...initial });

    // 2. Load initial snapshot (last 50 records per patient) from live_telemetry
    const loadSnapshot = async () => {
      console.log("[useClinicalStream] Loading snapshot for:", subjectIds);
      const { data, error } = await supabase
        .from("live_telemetry")
        .select("subject_id, itemid, valuenum, valueuom, charttime, is_outlier")
        .in("subject_id", subjectIds)
        .order("charttime", { ascending: true });

      if (error) {
        console.warn("[useClinicalStream] Snapshot load failed:", error.message);
        return;
      }

      console.log(`[useClinicalStream] Snapshot returned ${data?.length || 0} rows`);

      const snapshot: Record<number, VitalRecord[]> = {};
      subjectIds.forEach((id) => (snapshot[id] = []));

      (data || []).forEach((row) => {
        const sid = row.subject_id;
        if (snapshot[sid]) {
          snapshot[sid].push(row as VitalRecord);
          // Keep only the last 150 per patient (5 vitals * 30 points)
          if (snapshot[sid].length > 150) snapshot[sid].shift();
        }
      });

      console.log("[useClinicalStream] Final snapshot state:", snapshot);
      vitalsRef.current = snapshot;
      setVitals({ ...snapshot });
    };

    loadSnapshot();

    // 3. Real-time subscription for new inserts
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
          const rec = payload.new as VitalRecord;
          const sid = rec.subject_id;
          // console.log("[useClinicalStream] Received INSERT:", rec);
          if (!subjectIds.includes(sid)) return;

          const current = [...(vitalsRef.current[sid] || [])];
          current.push(rec);
          if (current.length > 150) current.shift();
          vitalsRef.current[sid] = current;
          
          // Send to AI pipeline for real-time analysis
          sendToAIPipeline(rec);
        }
      )
      .subscribe((status) => {
        console.log("[useClinicalStream] Subscription status:", status);
      });

    // 4. Sync ref → state every 500ms (smooth but not thrashing)
    let syncCount = 0;
    const syncInterval = setInterval(() => {
      syncCount++;
      if (syncCount % 10 === 0) {
        console.log("[useClinicalStream] Syncing UI state, total patients:", Object.keys(vitalsRef.current).length);
      }
      setVitals({ ...vitalsRef.current });
    }, 500);

    return () => {
      console.log("[useClinicalStream] Cleanup");
      supabase.removeChannel(channel);
      clearInterval(syncInterval);
    };
  }, [subjectIds.join(",")]);

  return { vitals };
}
