import asyncio
import os
import platform
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event, select

from app.core.database import Base
from app.models.fingerprint import MediaFingerprint
from app.matching.candidate_retrieval import candidate_retrieval

def generate_synthetic_fingerprints(count: int) -> List[MediaFingerprint]:
    np.random.seed(42)
    fingerprints = []
    for i in range(count):
        # Generate random 64-bit hex hash
        p_val = np.random.randint(0, 2**32, dtype=np.uint32)
        p_val2 = np.random.randint(0, 2**32, dtype=np.uint32)
        phash_hex = f"{p_val:08x}{p_val2:08x}"
        
        d_val = np.random.randint(0, 2**32, dtype=np.uint32)
        d_val2 = np.random.randint(0, 2**32, dtype=np.uint32)
        dhash_hex = f"{d_val:08x}{d_val2:08x}"

        sha256 = f"asset_{i:06d}_" + "a" * 48

        fp = MediaFingerprint(
            media_asset_id=f"media_asset_{i:06d}",
            algorithm_name="PerceptualHasherSuite",
            algorithm_version="1.0.0",
            preprocessing_version="PREPROCESS-V1",
            parameters={"hash_size": 8},
            sha256_hash=sha256,
            phash_hex=phash_hex,
            dhash_hex=dhash_hex,
            ahash_hex=phash_hex,
            colorhash_hex=phash_hex,
            orb_keypoints_count=150,
            orb_descriptor_rel_path=None,
            indexing_status="INDEXED"
        )
        fingerprints.append(fp)
    return fingerprints

async def run_benchmark():
    print("=" * 70)
    print("TRUTHNET HISTORICAL INDEX CANDIDATE RETRIEVAL BENCHMARK")
    print(f"Platform: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {platform.python_version()} | Processor: {platform.processor() or 'CPU'}")
    print("Method: Exact SHA-256 lookup + Linear Bounded Hamming Scan (Threshold = 12)")
    print("=" * 70)

    sizes = [100, 1000, 10000]
    results = []

    for n in sizes:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
        @event.listens_for(engine.sync_engine, "connect")
        def set_pragmas(dbapi_conn, _):
            c = dbapi_conn.cursor()
            c.execute("PRAGMA journal_mode=WAL;")
            c.execute("PRAGMA synchronous=NORMAL;")
            c.close()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

        # Populate synthetic index
        t_pop_start = time.perf_counter()
        async with session_factory() as session:
            fps = generate_synthetic_fingerprints(n)
            session.add_all(fps)
            await session.commit()
        t_pop_ms = (time.perf_counter() - t_pop_start) * 1000.0

        # Run 20 query repetitions
        repetitions = 20
        query_latencies = []
        candidates_counts = []

        target_fp = {
            "sha256_hash": "query_asset_target_nonexistent",
            "phash_hex": "123456789abcdef0",
            "dhash_hex": "0fedcba987654321"
        }

        async with session_factory() as session:
            for rep in range(repetitions):
                t0 = time.perf_counter()
                cands, telemetry = await candidate_retrieval.find_candidates(
                    db_session=session,
                    target_fingerprint=target_fp,
                    max_hamming=12
                )
                dt = (time.perf_counter() - t0) * 1000.0
                query_latencies.append(dt)
                candidates_counts.append(len(cands))

        mean_lat = float(np.mean(query_latencies))
        min_lat = float(np.min(query_latencies))
        max_lat = float(np.max(query_latencies))
        p95_lat = float(np.percentile(query_latencies, 95))
        throughput_qps = 1000.0 / mean_lat if mean_lat > 0 else 0.0

        db_size_kb = Path(db_path).stat().st_size / 1024.0

        results.append({
            "index_size": n,
            "db_size_kb": round(db_size_kb, 1),
            "pop_latency_ms": round(t_pop_ms, 1),
            "mean_ms": round(mean_lat, 2),
            "min_ms": round(min_lat, 2),
            "max_ms": round(max_lat, 2),
            "p95_ms": round(p95_lat, 2),
            "qps": round(throughput_qps, 1)
        })

        await engine.dispose()
        Path(db_path).unlink(missing_ok=True)
        Path(f"{db_path}-wal").unlink(missing_ok=True)
        Path(f"{db_path}-shm").unlink(missing_ok=True)

    print("\n--- EMPIRICAL RETRIEVAL BENCHMARK TABLE ---")
    print(f"{'Index Size':>10} | {'DB Size (KB)':>12} | {'Mean (ms)':>10} | {'Min (ms)':>9} | {'Max (ms)':>9} | {'P95 (ms)':>9} | {'Throughput (QPS)':>16}")
    print("-" * 88)
    for r in results:
        print(f"{r['index_size']:>10d} | {r['db_size_kb']:>12.1f} | {r['mean_ms']:>10.2f} | {r['min_ms']:>9.2f} | {r['max_ms']:>9.2f} | {r['p95_ms']:>9.2f} | {r['qps']:>16.1f}")
    print("-" * 88)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
