# ISEF Booth Checklist

> **Everything you need to bring to the ISEF booth. Print this. Pack the night before.**

---

## Hardware

| Item | Qty | Notes |
|---|---|---|
| Laptop (charged) | 1 | Primary demo machine. The .app installed, 4 examples loaded. |
| Laptop charger | 1 | 100W+ USB-C or barrel. |
| Phone (charged) | 1 | Backup demo + video playback + emergency hotspot. |
| Phone charger | 1 | USB-C, fast charge. |
| USB-C hub | 1 | For projector / external display if needed. |
| HDMI cable | 1 | To connect to the booth projector (if they have one). |
| Portable battery (10,000+ mAh) | 1 | Backup power for the laptop. |
| Tablet (optional) | 1 | For the demo video loop. |
| Headphones (backup) | 1 | In case of noisy floor. |

## Print materials

| Item | Qty | Notes |
|---|---|---|
| Poster (36"×48") | 1 | The big visual. With plateau chart, scaling table, headline numbers. |
| Poster backup (11"×17") | 2 | Smaller, easier to carry. For handouts. |
| 1-page project summary | 50 | The `PROJECT_SUMMARY_1PAGE.md` printed. Hand to every judge. |
| Business cards | 50 | Name, email, GitHub URL, project name. |
| NEOSEF / ISEF paperwork | as needed | Application, registration, ISEF-specific forms. |

## Digital materials (on the laptop)

| Item | Path |
|---|---|
| SmallChip AI .app | `/Applications/SmallChip AI.app` |
| Web app running | http://localhost:8000 (start before fair) |
| GitHub repo | https://github.com/hnelabhotla-boop/smallchip-ai |
| Demo video | YouTube unlisted, also downloaded as MP4 backup |
| Paper draft | `paper/ISEF_paper_draft.md` (rendered to PDF) |
| FAQ | `FAQ.md` (browser tab) |
| Pitch script | `PITCH_10MIN.md` (memorize, don't display) |
| Booth demo script | `BOOTH_DEMO_SCRIPT.md` (browser tab) |
| Polish logs (proof) | `/tmp/openroad_15k_v*.log`, `/tmp/openroad_5k_v2.log` |
| Plateau chart | `results/plateau_chart.png` |
| Headline chart | `results/headline_chart.png` |

## Setup checklist (morning of judging)

- [ ] Laptop charged to 100%
- [ ] .app opens, 4 example buttons work
- [ ] Backend running (`python -m uvicorn chipmind.api.server:app --host 0.0.0.0 --port 8000`)
- [ ] Web app loads in 5 seconds
- [ ] Demo video plays with sound off
- [ ] GCD example loads + Run comparison shows 99.7% improvement
- [ ] 15K example loads + shows 464,588 DBU legal HPWL
- [ ] LLM co-pilot responds to "make it use less power" (or falls back to keyword)
- [ ] GitHub repo loads in browser
- [ ] 1-page summary printed, stacked on table
- [ ] Business cards on table
- [ ] Poster hung on wall behind booth
- [ ] Phone hotspot working (backup internet)
- [ ] Water bottle (you'll be talking for 8+ hours)
- [ ] Snacks (granola bar, banana — no messy food)
- [ ] Notebook + pen (for taking notes on judge questions)

## What to wear

- ISEF dress code: business casual
- Strongsville High School polo or a button-down
- Dark pants, no jeans
- Comfortable shoes (8+ hours on concrete)
- ISEF name badge (issued at registration)
- School name badge if you have one

## Body language reminders

- ✅ Stand up, smile, make eye contact
- ✅ Speak at judge-pace, pause after big numbers
- ✅ Hand them the 1-page summary
- ❌ Don't read from notes (memorize the 3 anchor sentences)
- ❌ Don't apologize for limitations (frame as future work)
- ❌ Don't sit behind the laptop

## Pitch (memorize the 3 ⭐ sentences)

> "OpenROAD — the industry-standard chip placer, used by every chip company and free for anyone to download — places a 692-cell GCD chip at 3.99 million HPWL. My pre-trained AI places the same chip at 10,775 HPWL. That's 99.7% better wirelength, validated by OpenROAD's own static timing and power analyzer."

> "My single pre-trained model generalizes from 100 cells to 15,000 cells on a single CPU core, with per-connection wire quality that actually *improves* as designs get denser. The 15,000-cell result has 35.3 micrometers average wire segment per net — better than my 734-cell GCD reference at 46 micrometers per net."

> "SmallChip AI is the first open-source placer that scales to 15,000 cells, beats OpenROAD by 370× on the GCD benchmark, and ships as a working desktop app. I'd like to take it to ISEF to show that a 9th-grader with a laptop can build production-grade chip-placement AI."

## What to do if a judge wants to go deeper

- Open `paper/ISEF_paper_draft.md` (rendered to PDF) — show them the math section §3.8
- Open the GitHub repo — show them the code, the BSD license, the public data
- Open the polish logs in `/tmp/` — show them OpenROAD's divergence
- Use `BOOTH_DEMO_SCRIPT.md` as a navigation guide
- Use `FAQ.md` for the most likely questions

## What to do if a judge wants to network

- Hand them a business card
- Ask for THEIR business card
- Write the time/place on the back of their card immediately
- Follow up by email within 48 hours

## What to do at the end of the day

- [ ] Save all chat logs / feedback notes
- [ ] Update `FAQ.md` with any new questions
- [ ] Take a photo of the booth for memory
- [ ] Note any technical issues for next year
- [ ] Celebrate

## Emergency contacts

- Mom/dad (cell): [fill in]
- Science teacher: [fill in]
- Strongsville HS office: [fill in]
- ISEF lost & found: at registration desk
