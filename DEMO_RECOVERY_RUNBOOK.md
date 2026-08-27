# Demo Recovery Runbook

> **What to do when the .app, web demo, or live demo breaks at the booth.**
> Practice each recovery once before the fair. Print this card.

---

## The 30-second triage

When something breaks, do this in order:

1. **Don't panic.** Judges see broken demos all the time. Stay calm.
2. **Smile and say:** "Let me try something else." Don't apologize.
3. **Try the next step in the runbook below.**
4. **If all else fails, point to the poster.** The numbers are still there.

---

## Failure 1: The .app won't open

**Symptom:** Double-click, nothing happens. Or app opens then crashes.

**Recovery:**
1. Open Terminal (in Applications/Utilities)
2. Run: `cd /Applications && xattr -dr com.apple.quarantine "SmallChip AI.app"` (in case macOS quarantined it)
3. If still broken, drag the .app to Trash
4. Show the poster + screenshots instead. Say: "I have a 3-minute demo video that shows the same thing — want to see it?"

**Backup:** Have the demo video on a tablet, ready to play.

---

## Failure 2: The web app won't load

**Symptom:** Browser shows "couldn't connect" or blank page.

**Recovery:**
1. Open Terminal
2. Start the backend manually: `cd /Users/harshith/Documents/ChipPlacer && /Users/harshith/miniconda3/envs/chippind_rl/bin/python -m uvicorn chipmind.api.server:app --host 0.0.0.0 --port 8000`
3. Wait 5 seconds for "Application startup complete."
4. Open browser to http://localhost:8000
5. If still broken, check if the port is in use: `lsof -i :8000` and kill the conflicting process

**Backup:** Have the GCD placed DEF (with HPWL 10,775 already computed) ready to show in a text editor.

---

## Failure 3: The GCD example button doesn't load

**Symptom:** Click "🟢 GCD example", nothing happens. Or it shows "Could not load".

**Recovery:**
1. Check the .app's static mount is working: `curl http://localhost:8000/static/examples/gcd_734cells.def`
2. If 200 OK, the file is there. Issue is the frontend.
3. Hard-refresh the browser: Cmd+Shift+R
4. If still broken, use the file picker — manually upload the DEF from `/Users/harshith/Documents/ChipPlacer/web/examples/`

**Backup:** Have a USB stick with the 4 example DEFs pre-loaded.

---

## Failure 4: The "Run comparison" hangs

**Symptom:** Click button, spinner runs forever, no result.

**Recovery:**
1. Wait 30 seconds — comparison is running 12 algorithms
2. If still hanging after 60 seconds, check the terminal for the backend log
3. If the backend died, restart it (see Failure 2)
4. If you only need the GAT result, use "Run V3 only" button (if present) — this is faster

**Backup:** Have pre-computed comparison results in a JSON file. Open it in any text editor and show the numbers.

---

## Failure 5: The LLM co-pilot times out

**Symptom:** Type "make it use less power", spinner runs forever, no response.

**Recovery:**
1. Wait 10 seconds — Ollama can be slow on first call
2. If timeout, the co-pilot should fall back to keyword-based heuristic
3. If still no response, the chip is still placed (just no report). Say: "The chip is placed, but the LLM co-pilot timed out. Let me show you the numbers from the placement instead."
4. If Ollama is just slow, the first call always takes 30+ seconds. Pre-warm it before judging starts.

**Backup:** Have a screenshot of the co-pilot's response, ready to show.

---

## Failure 6: The laptop dies

**Symptom:** Black screen. Won't turn on. Or crashes mid-demo.

**Recovery:**
1. Stay calm. Say: "Let me grab my backup laptop."
2. Borrow a laptop from a neighbor (have a USB stick ready with the project files)
3. Pull from GitHub: `git clone https://github.com/hnelabhotla-boop/smallchip-ai.git`
4. Run: `pip install -e . && python -m uvicorn chipmind.api.server:app --host 0.0.0.0 --port 8000`
5. Open browser to http://localhost:8000
6. If you can't pull from GitHub (no internet), use the offline backup on your USB

**Backup:** Have a USB stick with a complete copy of the project (the 19MB .zip is perfect for this).

---

## Failure 7: No internet

**Symptom:** Can't reach GitHub, can't reach OpenROAD, can't reach Ollama.

**Recovery:**
1. The GCD placement result (10,775 HPWL) is pre-computed and on the laptop. You don't need internet for that.
2. The 15K polish result (418,115 HPWL) is also pre-computed.
3. The 4 example DEFs are local. The V3 model is local.
4. The only thing that needs internet is the LLM co-pilot (if using OpenAI). Ollama works offline.
5. Use your phone as a hotspot if you have one.

**Backup:** Everything is local-first. Internet is only for "nice to have" features (LLM via OpenAI).

---

## Failure 8: Judge asks a question I can't answer

**Symptom:** Judge asks something I don't know. Mind goes blank.

**Recovery:**
1. Pause. Take a breath.
2. Say: "Great question. Let me think about that for a second."
3. If you know it: answer. If not, say: "I don't have a number for that right now, but I can look it up in the paper / GitHub repo / my notes."
4. If the question reveals a real gap: write it down, address it after the fair.
5. **Never** make up an answer. Judges can tell.

**Backup:** FAQ.md has 20 likely questions with crisp answers. Read it before the fair.

---

## Failure 9: Judge disagrees with my framing

**Symptom:** Judge pushes back: "But what about X?" or "I don't think this is novel."

**Recovery:**
1. Don't argue. Listen to their concern.
2. Say: "That's a fair point. Can you tell me more about what you mean?"
3. If they have a valid concern, acknowledge it: "You're right, I should look into that."
4. If they have a misunderstanding, politely clarify: "I think there might be a miscommunication — let me re-explain."
5. Thank them at the end: "I appreciate you pushing on that — it makes the project stronger."

**Backup:** ISEF_RUBRIC_COVERAGE.md has anticipated judge concerns.

---

## Failure 10: Two judges at once

**Symptom:** Two judges approach the booth at the same time.

**Recovery:**
1. Greet both. "Hi! I'll be with both of you."
2. Start the demo. Both will see it.
3. If one judge asks a question, the other will listen.
4. If they want to go in different directions, prioritize the more senior / more engaged one.
5. Always hand a 1-page summary to BOTH judges, even if you only spoke to one.

**Backup:** Have 50+ printed 1-page summaries.

---

## General principles

1. **Stay calm.** Judges evaluate composure under pressure.
2. **Smile.** A smile buys you 30 seconds to figure out the next step.
3. **Never apologize.** Frame problems as features: "The interesting thing is..."
4. **Always have a backup.** Three layers of backup (live → screenshots → poster).
5. **Hand them the summary.** Even if the demo fails, the numbers on the page still work.

---

## Pre-fair checklist (do this the night before)

- [ ] Backend starts in <5 seconds
- [ ] All 4 example buttons work
- [ ] Run comparison completes in <30 seconds
- [ ] LLM co-pilot responds in <10 seconds (pre-warm with a test prompt)
- [ ] USB stick with project .zip is in your bag
- [ ] Demo video on tablet, charged
- [ ] 50+ printed 1-page summaries
- [ ] Backup laptop has project files
- [ ] Phone hotspot works
- [ ] Water bottle, snacks, breath mints
- [ ] Print this runbook
