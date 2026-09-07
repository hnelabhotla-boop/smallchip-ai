"""
post_cloud_update.py — When 100M cloud run finishes, this auto-updates:
1. arxiv preprint (the §4.5 100M scaling table)
2. README headline numbers
3. The scaling chart PNG
4. Git commit + push

Usage: python3 scripts/post_cloud_update.py
Inputs: results/scaling_100m_cloud.json (from cloud run)
Outputs: paper/arxiv_preprint.md, results/scaling_100m_cloud_chart.png, git push
"""
import json
import sys
import re
from pathlib import Path

REPO = Path("/Users/harshith/Documents/ChipPlacer")
CLOUD_JSON = REPO / "results/scaling_100m_cloud.json"
ARXIV_MD = REPO / "paper" / "arxiv_preprint.md"
README_MD = REPO / "README.md"
CHART_PY = REPO / "scripts/make_scaling_chart_v3.py"


def load_cloud_results():
    if not CLOUD_JSON.exists():
        print(f"[FAIL] {CLOUD_JSON} not found. Run cloud_run_100m.sh first.")
        sys.exit(1)
    with open(CLOUD_JSON) as f:
        data = json.load(f)
    return [r for r in data["results"] if "error" not in r]


def make_table_rows(results):
    """Generate markdown table rows from cloud results."""
    rows = []
    for r in results:
        rows.append(
            f"| {r['label']} | {r['n_cells']:,} | {r['n_nets']:,} | "
            f"{r['n_blocks']:,} | {r['build_time_s']:.2f}s | "
            f"{r['per_net_hpwl_dbu']:,.0f} |"
        )
    return "\n".join(rows)


def update_arxiv(results):
    """Update §4.5 100M scaling table in arxiv preprint."""
    if not ARXIV_MD.exists():
        print(f"[WARN] {ARXIV_MD} not found, skipping arxiv update")
        return False
    with open(ARXIV_MD) as f:
        text = f.read()
    new_rows = make_table_rows(results)
    # Find the table that starts with "| Scale | Cells |" and contains "100M-Cell Scaling"
    pattern = r"(\| Scale \|.*?\|)([\s\S]*?)(\n\n### 4\.6)"
    m = re.search(pattern, text)
    if not m:
        print("[WARN] Could not find §4.5 table in arxiv, skipping")
        return False
    header = m.group(1)
    after = m.group(3)
    new_section = header + "\n" + new_rows + after
    new_text = text[:m.start()] + new_section + text[m.end():]
    with open(ARXIV_MD, "w") as f:
        f.write(new_text)
    print(f"[OK] Updated {ARXIV_MD}")
    return True


def update_readme(results):
    """Update README with new scaling numbers."""
    if not README_MD.exists():
        print(f"[WARN] {README_MD} not found, skipping README update")
        return False
    with open(README_MD) as f:
        text = f.read()
    # Find the scaling line if it exists
    new_line = ""
    for r in results:
        if r["n_cells"] == 100_000_000:
            new_line = f"**100M cells PROVEN: {r['per_net_hpwl_dbu']:,.0f} DBU/net**"
            break
    if not new_line:
        for r in results:
            if r["n_cells"] == max(x["n_cells"] for x in results):
                new_line = f"**Largest: {r['n_cells']:,} cells at {r['per_net_hpwl_dbu']:,.0f} DBU/net**"
                break
    if not new_line:
        return False
    # Add a line near the top under any existing headline
    if "100M cells PROVEN" in text or "Largest:" in text:
        # Replace existing
        text = re.sub(r"\*\*100M cells PROVEN:.*?\*\*", new_line, text)
        text = re.sub(r"\*\*Largest:.*?\*\*", new_line, text)
    else:
        # Insert after first heading
        text = re.sub(r"(# SmallChip AI[^\n]*\n)", f"\\1\n{new_line}\n", text, count=1)
    with open(README_MD, "w") as f:
        f.write(text)
    print(f"[OK] Updated {README_MD}")
    return True


def regenerate_chart(results):
    """Regenerate the scaling chart with cloud data."""
    # Combine cloud results with prior numpy data if any
    numpy_json = REPO / "results/scaling_100m_numpy_test.json"
    combined = list(results)
    if numpy_json.exists():
        with open(numpy_json) as f:
            for r in json.load(f).get("results", []):
                if "error" not in r and r not in combined:
                    combined.append(r)
    out_json = REPO / "results/scaling_100m_cloud_chart_data.json"
    with open(out_json, "w") as f:
        json.dump({"results": combined}, f, indent=2)
    # Run the chart script with the combined data
    import subprocess
    try:
        subprocess.run(
            ["python3", str(CHART_PY), "--input", str(out_json), "--output",
             str(REPO / "results/scaling_100m_cloud_chart.png")],
            check=True, capture_output=True, text=True, timeout=30,
        )
        print(f"[OK] Regenerated chart")
        return True
    except Exception as e:
        print(f"[WARN] Chart regen failed: {e}")
        return False


def git_commit_push():
    """Commit and push all changes."""
    import subprocess
    try:
        subprocess.run(["git", "add", "-A"], cwd=REPO, check=True, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", "100M cells PROVEN — auto-update from cloud run"],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        )
        print(f"[GIT] {result.stdout.strip()}")
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        )
        print(f"[GIT] {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"[WARN] Git push failed: {e}")
        return False


def main():
    print("=" * 60)
    print("  Post-cloud auto-update")
    print("=" * 60)
    results = load_cloud_results()
    print(f"Loaded {len(results)} successful cloud runs")
    for r in results:
        print(f"  {r['label']:>10}: {r['n_cells']:>12,} cells, {r['per_net_hpwl_dbu']:>12,.0f} DBU/net")
    print()
    update_arxiv(results)
    update_readme(results)
    regenerate_chart(results)
    git_commit_push()
    print()
    print("=" * 60)
    print("  DONE. All updates pushed to GitHub.")
    print("=" * 60)


if __name__ == "__main__":
    main()
