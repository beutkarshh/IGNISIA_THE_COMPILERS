"""
Parallel Vitals Ingestion Engine  —  IGNISIA ICU
==================================================
Every INTERVAL_SEC seconds, reads the next BATCH_SIZE chartevents rows
per patient (in parallel), tags outliers, and writes to live_telemetry.
The frontend's useClinicalStream picks up inserts via Supabase Realtime.

Run:  python -m ingestor.run
"""

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Optional

from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
INTERVAL_SEC: int = int(os.getenv("INGEST_INTERVAL_SEC", "10"))
BATCH_SIZE:   int = int(os.getenv("INGEST_BATCH_SIZE",   "3"))
MAX_TELEMETRY_ROWS: int = 10_000

# Vital sign itemids to ingest (MIMIC-III d_items codes)
VITAL_ITEMIDS: list[int] = [
    211, 220045,                              # Heart Rate
    456, 52, 6702, 443, 220052, 220181, 225312,  # MAP
    51, 442, 455, 6701, 220179, 220050,       # Systolic BP
    646, 220277,                              # SpO2
    615, 618, 220210, 224690,                 # Respiratory Rate
    223761, 678,                              # Temperature
]

# Per-patient cursor: last charttime ingested (advances every tick)
_cursors: dict[int, Optional[str]] = {}


def make_client() -> Client:
    return create_client(
        SUPABASE_URL, SUPABASE_KEY,
        options=ClientOptions(auto_refresh_token=False, persist_session=False)
    )


# ── Outlier thresholds ───────────────────────────────────────────────────────
_THRESHOLDS: dict[int, tuple[float, float]] = {
    211:    (40,  160),  220045: (40,  160),   # HR
    456:    (60,  110),  52:     (60,  110),   # MAP
    6702:   (60,  110),  443:    (60,  110),
    220052: (60,  110),  220181: (60,  110),  225312: (60, 110),
    51:     (80,  180),  442:    (80,  180),   # SBP
    455:    (80,  180),  6701:   (80,  180),
    220179: (80,  180),  220050: (80,  180),
    646:    (90,  100),  220277: (90,  100),   # SpO2
    615:    (8,   30),   618:    (8,   30),    # RR
    220210: (8,   30),   224690: (8,   30),
    223761: (35.5, 38.5),  678:  (96,  101),  # Temp
}

def is_outlier(itemid: int, value: float) -> bool:
    bounds = _THRESHOLDS.get(itemid)
    if bounds is None:
        return False
    lo, hi = bounds
    return not (lo <= value <= hi)


# ── Fetch one patient's next batch from chartevents ─────────────────────────
# We run 5 parallel queries — one for each vital category — to guarantee every category updates per tick.
async def fetch_category(db: Client, subject_id: int, itemids: list[int]) -> Optional[dict]:
    cursor = _cursors.get(subject_id)
    q = (
        db.table("chartevents")
        .select("subject_id, hadm_id, itemid, charttime, valuenum, valueuom")
        .eq("subject_id", subject_id)
        .in_("itemid", itemids)
        .not_.is_("valuenum", "null")
        .order("charttime", desc=False)
        .limit(1)
    )
    if cursor:
        q = q.gt("charttime", cursor)
        
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(None, lambda: q.execute())
    data = resp.data or []
    return data[0] if data else None

async def fetch_chartevents_async(db: Client, subject_id: int) -> list[dict]:
    # Group itemids by clinical category
    categories = [
        [211, 220045],                              # HR
        [456, 52, 6702, 443, 220052, 220181, 225312],  # MAP
        [646, 220277],                              # SpO2
        [615, 618, 220210, 224690],                 # RR
        [223761, 678]                               # Temp
    ]
    
    # Fetch 1 latest reading for each category
    tasks = [fetch_category(db, subject_id, cat) for cat in categories]
    results = await asyncio.gather(*tasks)
    
    rows = [r for r in results if r is not None]
    
    # Update cursor to the MAXIMUM charttime found across all categories this tick
    if rows:
        max_time = max(r["charttime"] for r in rows)
        _cursors[subject_id] = max_time
    else:
        # None of the categories had data after cursor -> reset to beginning
        _cursors[subject_id] = None

    return rows


# ── Write rows to live_telemetry ─────────────────────────────────────────────
def write_to_telemetry(db: Client, rows: list[dict]) -> int:
    if not rows:
        return 0

    now = datetime.now(timezone.utc).isoformat()
    records = []
    for r in rows:
        val = r.get("valuenum")
        if val is None:
            continue
        records.append({
            "subject_id": r["subject_id"],
            "hadm_id":    r.get("hadm_id"),
            "itemid":     r["itemid"],
            "valuenum":   float(val),
            "valueuom":   r.get("valueuom", ""),
            "charttime":  r["charttime"],
            "is_outlier": is_outlier(r["itemid"], float(val)),
            "created_at": now,
        })

    if records:
        db.table("live_telemetry").insert(records).execute()
    return len(records)


# ── Prune old rows to keep table lean ───────────────────────────────────────
def prune_old_rows(db: Client):
    try:
        resp = db.table("live_telemetry").select("id", count="exact").execute()
        total = resp.count or 0
        if total > MAX_TELEMETRY_ROWS:
            excess = total - MAX_TELEMETRY_ROWS
            cutoff = (
                db.table("live_telemetry")
                .select("id")
                .order("id", desc=False)
                .limit(excess)
                .execute()
            )
            ids = [r["id"] for r in (cutoff.data or [])]
            if ids:
                db.table("live_telemetry").delete().in_("id", ids).execute()
                print(f"  🧹 Pruned {len(ids)} old rows")
    except Exception as e:
        print(f"  ⚠️  Prune error: {e}")


# ── Per-patient async task ───────────────────────────────────────────────────
async def ingest_one_patient(db: Client, subject_id: int) -> int:
    loop = asyncio.get_event_loop()
    rows  = await fetch_chartevents_async(db, subject_id)
    count = await loop.run_in_executor(None, write_to_telemetry, db, rows)
    return count


# ── Main ingestion loop ──────────────────────────────────────────────────────
async def ingestion_loop():
    db = make_client()

    print(f"\n{'═'*56}")
    print(f"  🏥  IGNISIA Vitals Ingestor")
    print(f"  📡  {SUPABASE_URL}")
    print(f"  ⏱   interval={INTERVAL_SEC}s   batch={BATCH_SIZE} rows/patient/tick")
    print(f"{'═'*56}\n")

    # Sanity-check tables
    try:
        db.table("chartevents").select("subject_id").limit(1).execute()
        print("  ✅  chartevents  : accessible")
    except Exception as e:
        print(f"  ❌  chartevents unreachable: {e}")
        return

    try:
        db.table("live_telemetry").select("id").limit(1).execute()
        print("  ✅  live_telemetry: accessible")
    except Exception as e:
        print(f"  ❌  live_telemetry unreachable: {e}")
        return

    # Fetch all patient IDs once (re-fetch every 50 ticks in case new patients added)
    patient_ids: list[int] = []
    tick = 0

    while True:
        tick += 1
        t0 = time.monotonic()

        if tick == 1 or tick % 50 == 0:
            resp = db.table("patients").select("subject_id").execute()
            patient_ids = [r["subject_id"] for r in (resp.data or [])]
            print(f"\n  👥  Tracking {len(patient_ids)} patients")

        if not patient_ids:
            print("  ⚠️  No patients found. Retrying in 30s...")
            await asyncio.sleep(30)
            continue

        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n[Tick {tick:04d}]  {ts}  —  {len(patient_ids)} patients in parallel")

        # ALL patients run concurrently
        tasks  = [ingest_one_patient(db, sid) for sid in patient_ids]
        counts = await asyncio.gather(*tasks, return_exceptions=True)

        total = 0
        for sid, result in zip(patient_ids, counts):
            if isinstance(result, Exception):
                print(f"    [{sid}] ❌  {result}")
            elif result > 0:
                print(f"    [{sid}] ✓  {result} rows")
                total += result

        if tick % 20 == 0:
            prune_old_rows(db)

        elapsed = time.monotonic() - t0
        sleep   = max(0.0, INTERVAL_SEC - elapsed)
        print(f"  → {total} total rows written in {elapsed:.2f}s — sleeping {sleep:.1f}s")
        await asyncio.sleep(sleep)
