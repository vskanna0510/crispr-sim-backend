import asyncio
import time
import statistics
import sys
import os
import httpx

sys.path.insert(0, os.path.dirname(__file__))

TARGET_URL = "http://127.0.0.1:8000"
CONCURRENT_USERS = 100
TEST_DURATION_SECONDS = 60

TEST_SCENARIOS = [
    ("GET", "/health", None),
    ("GET", "/", None),
    ("POST", "/crispr/scan", {"sequence": "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCAGG", "cas_type": "cas9"}),
    ("POST", "/crispr/cut", {"sequence": "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCAGG", "pam_start": 44, "cas_type": "cas9"}),
]

latencies = []
endpoint_stats = {path: {"latencies": [], "success": 0, "fail": 0} for _, path, _ in TEST_SCENARIOS}
total_requests = 0
successful_requests = 0
failed_requests = 0

async def user_worker(user_id: int, stop_time: float, client: httpx.AsyncClient):
    global total_requests, successful_requests, failed_requests
    scenario_idx = user_id % len(TEST_SCENARIOS)
    
    while time.time() < stop_time:
        method, path, body = TEST_SCENARIOS[scenario_idx]
        scenario_idx = (scenario_idx + 1) % len(TEST_SCENARIOS)
        
        start_t = time.perf_counter()
        try:
            if method == "GET":
                resp = await client.get(path, timeout=10.0)
            else:
                resp = await client.post(path, json=body, timeout=10.0)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            
            if resp.status_code < 400:
                successful_requests += 1
                endpoint_stats[path]["success"] += 1
            else:
                failed_requests += 1
                endpoint_stats[path]["fail"] += 1
                
            latencies.append(elapsed_ms)
            endpoint_stats[path]["latencies"].append(elapsed_ms)
        except Exception:
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            failed_requests += 1
            endpoint_stats[path]["fail"] += 1
            latencies.append(elapsed_ms)
        
        total_requests += 1
        # Realistic user pacing (10ms pause)
        await asyncio.sleep(0.01)

async def main():
    print("=" * 60)
    print("CRISPR-Sim API Baseline / Load Test")
    print("=" * 60)
    print(f"Target Host      : {TARGET_URL}")
    print(f"Virtual Users    : {CONCURRENT_USERS}")
    print(f"Duration         : {TEST_DURATION_SECONDS} seconds")
    print("-" * 60)
    print("Running baseline load test for 1 minute...")
    
    start_time = time.time()
    stop_time = start_time + TEST_DURATION_SECONDS
    
    limits = httpx.Limits(max_keepalive_connections=200, max_connections=300)
    async with httpx.AsyncClient(base_url=TARGET_URL, limits=limits) as client:
        tasks = [user_worker(i, stop_time, client) for i in range(CONCURRENT_USERS)]
        await asyncio.gather(*tasks)
        
    total_duration = time.time() - start_time
    rps = total_requests / total_duration if total_duration > 0 else 0
    
    if not latencies:
        print("No requests completed.")
        return
        
    avg_lat = statistics.mean(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)
    median_lat = statistics.median(latencies)
    sorted_lat = sorted(latencies)
    p90 = sorted_lat[int(len(sorted_lat) * 0.90)]
    p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
    p99 = sorted_lat[int(len(sorted_lat) * 0.99)]
    error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0

    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS (Summary)")
    print("=" * 60)
    print(f"Total Requests Processed : {total_requests:,}")
    print(f"Successful Requests      : {successful_requests:,}")
    print(f"Failed Requests          : {failed_requests:,}")
    print(f"Error Rate               : {error_rate:.2f}%")
    print(f"Test Duration            : {total_duration:.2f} s")
    print(f"Requests per Second (RPS): {rps:.2f} req/sec")
    print("-" * 60)
    print("Response Time (Latency):")
    print(f"  * Fastest (Min)        : {min_lat:.2f} ms")
    print(f"  * Average (Mean)       : {avg_lat:.2f} ms")
    print(f"  * Median (p50)         : {median_lat:.2f} ms")
    print(f"  * 90th Percentile (p90): {p90:.2f} ms")
    print(f"  * 95th Percentile (p95): {p95:.2f} ms")
    print(f"  * 99th Percentile (p99): {p99:.2f} ms")
    print(f"  * Slowest (Max)        : {max_lat:.2f} ms")
    print("-" * 60)
    print("Breakdown by Endpoint:")
    print(f"{'Endpoint':<22} {'Requests':<10} {'RPS':<10} {'Avg (ms)':<10} {'p95 (ms)':<10} {'Errors':<8}")
    print("-" * 70)
    for path, data in endpoint_stats.items():
        cnt = len(data["latencies"])
        if cnt > 0:
            ep_avg = statistics.mean(data["latencies"])
            s_lat = sorted(data["latencies"])
            ep_p95 = s_lat[int(cnt * 0.95)]
            ep_rps = cnt / total_duration
            print(f"{path:<22} {cnt:<10} {ep_rps:<10.1f} {ep_avg:<10.2f} {ep_p95:<10.2f} {data['fail']:<8}")
        else:
            print(f"{path:<22} {0:<10} {0:<10.1f} {'N/A':<10} {'N/A':<10} {data['fail']:<8}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
