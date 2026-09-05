"""
Real-design hierarchical benchmark via the API.

Hits /api/hierarchical_place_real on the actual bigblue1 15K subset
at multiple block counts and captures the full results.
"""
import json
import time
from pathlib import Path

import urllib.request
import urllib.parse

API = "http://localhost:8000"
DEF_PATH = "/Users/harshith/Documents/RLChip_ISEF/results/bigblue1_15k_subset.def"
OUT = Path("/Users/harshith/Documents/ChipPlacer/results/real_hier_benchmark.json")


def run(n_blocks, cells_per_block, canvas_w=10000, canvas_h=10680):
    """POST to /api/hierarchical_place_real."""
    import mimetypes
    import uuid
    boundary = uuid.uuid4().hex
    body = []
    with open(DEF_PATH, "rb") as f:
        def_bytes = f.read()
    body.append(f"--{boundary}\r\n".encode())
    body.append(b'Content-Disposition: form-data; name="file"; filename="bigblue1_15k_subset.def"\r\n')
    body.append(b"Content-Type: application/octet-stream\r\n\r\n")
    body.append(def_bytes)
    body.append(b"\r\n")
    for k, v in [("n_blocks", n_blocks), ("cells_per_block", cells_per_block),
                 ("canvas_w", canvas_w), ("canvas_h", canvas_h)]:
        body.append(f"--{boundary}\r\n".encode())
        body.append(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        body.append(str(v).encode())
        body.append(b"\r\n")
    body.append(f"--{boundary}--\r\n".encode())
    payload = b"".join(body)
    req = urllib.request.Request(
        f"{API}/api/hierarchical_place_real",
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    client_time = time.time() - t0
    return data, client_time


def main():
    print("=" * 75)
    print("REAL HIERARCHICAL BENCHMARK (bigblue1 15K subset)")
    print("=" * 75)
    results = []
    configs = [
        (2, 7500, "2 blocks, 7500 cells/block"),
        (3, 5000, "3 blocks, 5000 cells/block"),
        (4, 3750, "4 blocks, 3750 cells/block"),
        (5, 3000, "5 blocks, 3000 cells/block"),
    ]
    for n_blocks, cells_per_block, label in configs:
        print(f"\n[{label}]")
        try:
            data, client_time = run(n_blocks, cells_per_block)
            per_net = data["total_hpwl_dbu"] / max(data["n_nets"], 1)
            result = {
                "label": label,
                "n_blocks": n_blocks,
                "cells_per_block": cells_per_block,
                "n_cells": data["n_cells"],
                "n_nets": data["n_nets"],
                "block_v3_times_ms": data["block_v3_times_ms"],
                "total_time_ms": data["total_time_ms"],
                "client_time_s": round(client_time, 2),
                "stitched_cells": data["stitched_cells"],
                "block_failures": data["block_failures"],
                "total_hpwl_dbu": data["total_hpwl_dbu"],
                "per_net_hpwl_dbu": round(per_net, 1),
            }
            results.append(result)
            print(f"  cells={data['n_cells']:,} nets={data['n_nets']:,} blocks={n_blocks}")
            print(f"  block_v3_times={data['block_v3_times_ms']} ms")
            print(f"  total_time={data['total_time_ms']} ms  client={client_time:.2f}s")
            print(f"  stitched={data['stitched_cells']}/{data['n_cells']}  failures={data['block_failures']}")
            print(f"  total_hpwl={data['total_hpwl_dbu']:,} DBU  per_net={per_net:,.0f} DBU/net")
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"label": label, "error": str(e)})
    # Summary
    print("\n" + "=" * 75)
    print("SUMMARY")
    print("=" * 75)
    print(f"{'Config':<30} {'Time(s)':>10} {'HPWL (M)':>12} {'DBU/net':>10} {'Status':>10}")
    print("-" * 75)
    for r in results:
        if "error" in r:
            print(f"{r['label']:<30} {'ERR':>10} {'-':>12} {'-':>10} {'FAIL':>10}")
        else:
            status = "OK" if r["block_failures"] == 0 and r["stitched_cells"] == r["n_cells"] else "WARN"
            print(f"{r['label']:<30} {r['total_time_ms']/1000:>10.1f} "
                  f"{r['total_hpwl_dbu']/1e6:>12.1f} {r['per_net_hpwl_dbu']:>10,.0f} {status:>10}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"benchmark": "real_hier_bigblue1_15k", "configs": results}, f, indent=2)
    print(f"\nSaved to {OUT}")


if __name__ == "__main__":
    main()
