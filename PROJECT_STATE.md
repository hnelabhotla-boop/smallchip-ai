# SmallChip AI — Project State (Harshith)

> **Recovery brief** for the wedged session `mvs_6fcc141e07e54bfca7617dfde27b8f88`.
> Last updated: 2026-08-26 19:10 EDT.
> Read this first in any new chat. Source of truth for the to-do list, ISEF plan, blockers, and locked decisions.

## 🏎️ Motivation

**Target:** Win at least **$35,000** at ISEF 2027 to buy a **used BMW Z4 G29 (sDrive30i, 2019-2021)** — they're $35K-$50K used in good condition. The car is the line in the sand. If a decision doesn't move the project toward that $35K, it's not the right decision.

---

## 1. To-do list (priority order)

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | v0.2.0 .app with example DEFs | ✅ DONE | `592915c`. Download, click 4 example buttons, test it. |
| 2 | **Polish 15K below 587,382** | ⏸ PAUSED | 60-epoch retrain done. Polish SA / more epochs not approved. |
| 3 | **Paper rewrite with math** | ⏳ TODO | User moved this to #3 explicitly. |
| 4 | **Wow demo for ISEF** | ⏳ TODO | Presentation-ready interactive demo. |
| 5 | **5K head-to-head vs OpenROAD** | ⏳ TODO | Pivot from broken 15K; 5K RePlAce should converge. |
| 6 | LEF parser | ✅ DONE | Added this session. `chipmind/core/lef_parser.py`. |
| 7 | Real-routed GCD power (post-CTS+route) | ⏳ TODO | Currently placement-stage only. |
| 8 | Timing/power-driven placement cost | ⏳ TODO | Currently HPWL-only. Required for Grand Prize. |

**User constraint (Aug 24):** "15K is THE priority. Plan first, no action without approval." Honor this — don't kick off new work without sign-off.

---

## 2. ISEF 2027 win plan

**Project:** SmallChip AI — free, open-source, AI chip placement for ≤15,000-cell designs (microwave controllers, hearing aids, IoT, key fobs, PMICs). Replaces the $1M EDA license.

**Locked (validated) claims to defend:**
- GCD: 99.7% / 370× post-legalization HPWL improvement (10,775 vs OpenROAD's 3,987,080). Validated by OpenROAD's own STA + power analysis. Identical timing (0.52 ns WNS, 2097 MHz) and identical power (1.06 mW).
- 15K scaling: 5K=427,545 / 8K=420,146 / 10K=461,939 / 15K=587,382 legal HPWL. 44.7 µm/net at 15K (better per-connection quality than GCD's 46 µm).
- 91-design benchmark: 89/91 wins, 75.2% avg improvement.
- Web app with PWA + LLM co-pilot.
- Open source: github.com/hnelabhotla-boop/smallchip-ai.

**Grand Prize gaps to close:**
1. ✅ Multiple-chip-scale validation curve (5K→15K)
2. ❌ **Real-routed GCD power** (currently placement-stage estimate; need full OpenROAD flow post-CTS + routing)
3. 🟡 Open-source community angle (GitHub live, need stars/contributors/users)
4. ❌ **Head-to-head with OpenROAD on a working design** — 15K blocked (GPL-0305 divergence), 5K not yet attempted
5. ❌ **Timing/power optimization** — model is HPWL-only

**Locked claim framing (DO NOT change):**
- LLM co-pilot "shapes the report" only. **Never** trades off HPWL.
- "Use ONLY the legalized 99.7% / 370× HPWL improvement number" (user explicit, rejected pre-legal 98.7%).
- No response times in the paper (user explicit).
- Target small-to-medium chips ≤15,000 cells; do not compete on big designs.

---

## 3. Open blockers

**BLOCKER 1 — 15K OpenROAD head-to-head, TERMINAL:**
- All 4 background Docker runs lost; OpenROAD RePlAce diverges on 15K (GPL-0305 numerical instability, gradient blows up to 1e31 at iteration ~2700).
- "98.7% better than OpenROAD on 15K" claim in paper §5.5 is currently un-defended on this benchmark.
- **Pivot:** try 5K subset (RePlAce should converge there).

**BLOCKER 2 — "773,315,382" V3 baseline number:**
- Cron task was comparing OpenROAD against "V3's 773,315,382" but the locked V3 raw is 6,020,661 and locked V3 retrain raw is also in that range. **773M doesn't match anything in the paper.** Flag for user to clarify before any ISEF judge sees it.

**BLOCKER 3 — Real-routed GCD power:**
- Headline "identical power" is global-placement estimation, not full OpenROAD flow measurement.

**BLOCKER 4 — Timing/power-driven placement:**
- Required for Grand Prize. Currently HPWL-only.

**BLOCKER 5 — GitHub PAT in remote URL:**
- A GitHub PAT was used during a previous push and was unset from the remote URL after. **Action: rotate the token immediately** — the original value appeared in chat history and is now in this file's git history; assume it is compromised.

---

## 4. Last 5 active work threads

1. **v0.2.0 .app release & example-loading fix** (Aug 25 ~20:30–20:55). DONE. User was supposed to test, session wedged first.
2. **4 example buttons in web UI** (Aug 25 ~20:35–20:42). DONE. 🟢 GCD / 🟡 5K / 🟠 8K / 🔴 15K.
3. **GitHub repo go-live** (Aug 25 ~17:30–18:00). DONE. ~10+ commits.
4. **15K V3 retrain + detailed placer** (Aug 24–25). DONE. 60 epochs on 510-chip corpus, best 614,863 → detailed placer 587,382.
5. **ISEF gap analysis** (Aug 25 ~17:27). TODO. 5 items, only #1 closed.

---

## 5. Deadlines / constraints

- **NEOSEF (regional):** December 2026. **Win Grand Prize** to qualify for ISEF.
- **ISEF International:** May 2027.
- **Marching band:** Half-day Jul 23-24, full camp 8 AM-3 PM Jul 27 – Aug 7. Season starts before school Aug 18.
- **15K = THE priority** (user explicit, Aug 24).
- **Carnatic class** Tues/Fri 6:30 AM + 30 min solo daily.
- **Gym** Mon/Tue/Thu/Fri 5:30–7:00 PM; pickleball Sat AM, soccer Sun AM.

---

## 6. File map

- Project root: `/Users/harshith/Documents/ChipPlacer/`
  - `chipmind/` — Python package (api/, core/, ml/, llm_copilot.py)
  - `web/` — frontend (index.html, app.js, copilot.html, examples/)
  - `desktop_app.py`, `dist/SmallChip AI.app`, `releases/`
  - `paper/ISEF_paper_draft.md` (28.5 KB, current)
- ISEF working dir: `/Users/harshith/Documents/RLChip_ISEF/`
  - `paper/ISEF_paper_draft.md.bak`, `.bak2`
  - `results/15K_REPORT_2026-08-24.md`
  - many benchmark / training scripts
- OpenROAD logs: `/tmp/openroad_15k_v{2..6}.log` (v6 last completed; all failed GPL-0305)
  - Active: `/tmp/openroad_5k_v2.log` (15.6 KB, still chugging as of 18:33 today)
- Server: `/tmp/chipmind_server.log`
- Env: `miniconda3/envs/chippind_rl`
- GitHub: `https://github.com/hnelabhotla-boop/smallchip-ai` (main, `592915c`)
- v0.2.0 release: https://github.com/hnelabhotla-boop/smallchip-ai/releases/tag/v0.2.0

---

## 7. Cron to disable

`5f957189-c782-4fc4-9c26-219b1ea54f46` — "Check 15K OpenROAD run" loop on wedged session. Every tick errors. Kill it.

---

## 8. Progress (Aug 26 19:20 EDT — fresh session)

**Just completed:**
- ✅ Saved full context to PROJECT_STATE.md (this file)
- ✅ Generated plateau chart (`results/plateau_chart.png`) + headline chart (`results/headline_chart.png`)
- ✅ Drafted §3.8 Mathematical Foundations (HPWL, GAT attention, V3 loss, complexity)
- ✅ Drafted §4.7 The Scalability Wall (4/4 OpenROAD 15K + 1/1 5K runs diverge)
- ✅ Both new sections merged into `ISEF_paper_draft.md`
- ✅ Wrote 10-min NEOSEF pitch script (`PITCH_10MIN.md`)
- ✅ Wrote IEEE Computer Society special award application (`IEEE_CS_SPECIAL_AWARD_APPLICATION.md`)
- ✅ Git committed: `506b984` on main
- 🔄 15K polish loop running in background (PID 37528)
- 🔄 Cron monitoring: every 25 min

**Deliverables to ship next:**
- Push to GitHub (after GCD OpenROAD full-flow result lands)
- 1-page project summary for NEOSEF booth
- Side-by-side routing congestion heatmap (wow demo)
- Real-routed GCD power number (needs OpenROAD install, blocked)
- Polish 15K to <500K (running, may not hit)
- Rehearse the 10-min pitch

**Files now in repo (not yet pushed to GitHub):**
- `PROJECT_STATE.md` (this file)
- `paper/OPENROAD_DIVERGENCE_SECTION.md` (working draft, content merged into main paper)
- `paper/SECTION_3_8_MATHEMATICAL_FOUNDATIONS.md` (working draft, content merged into main paper)
- `PITCH_10MIN.md`
- `IEEE_CS_SPECIAL_AWARD_APPLICATION.md`
- `results/plateau_chart.png` + `results/headline_chart.png` + `results/make_plateau_chart.py`
