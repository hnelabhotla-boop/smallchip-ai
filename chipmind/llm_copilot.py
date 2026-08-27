"""
LLM Chip Design Co-Pilot
========================
- Takes a chip netlist + user's plain-English request
- Uses an LLM (OpenAI API or local Ollama) to handle conversation
- Runs the GAT placer to get the best-possible chip
- Returns a redesigned chip + a human-readable report

LLM providers (auto-detected in order):
  1. OpenAI API (if OPENAI_API_KEY is set) — best quality, costs $$
  2. Local Ollama (if ollama serve is running) — free, offline
  3. Keyword fallback (no LLM) — last resort

Fact-vs-conversation split:
  - Templates provide factual content (HPWL defs, OpenROAD numbers, etc.)
  - LLM provides the conversational layer (greetings, empathy, tone, off-topic redirects)
  This keeps the LLM from hallucinating on niche technical facts.

Preference vector (5 dims, sums to 1):
  [hpwl, power, area, timing, congestion]
"""

import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# Try to import openai
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Preference vector interpretation helpers
PREF_LABELS = ["hpwl", "power", "area", "timing", "congestion"]

# Ollama default
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini")

# System prompt for the chip co-pilot LLM
CHIP_COPILOT_SYSTEM = """You are "ChipMind", an AI co-pilot for chip design (placement, routing, timing, power, area, congestion). You help a high-schooler named Harshith build a chip design tool for ISEF 2027. You are warm, technically accurate, and concise.

Rules:
- You ALWAYS defer to the structured data (HPWL, cell count, etc.) provided to you. Never invent technical numbers.
- For specific technical terms (HPWL, legalization, etc.) use the exact definitions provided in the conversation context.
- Stay focused on chip design. If the user goes off-topic, briefly empathize then redirect to chip work.
- Be conversational. Use 1-3 sentences usually. No bullet lists unless asked.
- You are running on local Ollama — keep responses short to stay snappy."""


# ------------------------------------------------------------------ #
# LLM provider detection + call helpers
# ------------------------------------------------------------------ #
def _has_openai() -> bool:
    return HAS_OPENAI and bool(os.environ.get("OPENAI_API_KEY"))


def _has_ollama() -> bool:
    try:
        req = urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=1)
        return req.status == 200
    except (urllib.error.URLError, OSError, ConnectionError):
        return False


def _ollama_chat(messages: List[Dict[str, str]], model: str = None,
                 temperature: float = 0.3, max_tokens: int = 250) -> Optional[str]:
    """Call local Ollama chat API. Returns None on failure."""
    if model is None:
        model = OLLAMA_MODEL
    try:
        data = json.dumps({
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat", data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            out = json.loads(resp.read().decode("utf-8"))
            content = out.get("message", {}).get("content", "").strip()
            if not content:
                print(f"[ollama] empty content. Full response: {json.dumps(out)[:300]}")
            return content or None
    except Exception as e:
        print(f"[ollama] error: {type(e).__name__}: {e}")
        return None


def _openai_chat(messages: List[Dict[str, str]], model: str = "gpt-4o-mini",
                 temperature: float = 0.3, max_tokens: int = 250) -> Optional[str]:
    """Call OpenAI chat API. Returns None on failure."""
    if not _has_openai():
        return None
    try:
        client = openai.OpenAI()
        resp = client.chat.completions.create(
            model=model, messages=messages, temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip() or None
    except Exception as e:
        print(f"[openai] error: {e}")
        return None


def _llm_chat(messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
    """Try OpenAI first, fall back to Ollama. Returns None if both fail."""
    out = _openai_chat(messages, **kwargs)
    if out is not None:
        return out
    return _ollama_chat(messages, **kwargs)


# ------------------------------------------------------------------ #
# Preference mapping
# ------------------------------------------------------------------ #
def default_preference() -> List[float]:
    """Equal weight to all 5 objectives."""
    return [0.2, 0.2, 0.2, 0.2, 0.2]


def keyword_to_preference(text: str):
    """Rule-based fallback: map keywords to preference weights.

    Robust to casual language (typos, slang, dropped words).

    Returns (preference, matched_keywords).
    """
    import re
    text = text.lower()
    # Normalize: strip punctuation, collapse repeated chars
    norm = re.sub(r"[^a-z0-9 ]", " ", text)
    norm = re.sub(r"(.)\1{2,}", r"\1", norm)  # loooow -> low
    norm = re.sub(r"\s+", " ", norm).strip()
    pref = default_preference()
    keywords = {
        # Power
        "low power": {"power": +0.4, "hpwl": +0.1},
        "less power": {"power": +0.4, "hpwl": +0.1},
        "lower power": {"power": +0.4, "hpwl": +0.1},
        "save power": {"power": +0.4, "hpwl": +0.1},
        "power": {"power": +0.2},
        "energy": {"power": +0.2},
        "battery": {"power": +0.3},
        "cool": {"power": +0.2, "congestion": +0.1},
        "thermal": {"power": +0.2},
        "watt": {"power": +0.2},
        # Area / die size
        "small": {"area": +0.4, "hpwl": +0.1},
        "smaller": {"area": +0.4, "hpwl": +0.1},
        "smaller die": {"area": +0.5, "hpwl": +0.1},
        "shrink": {"area": +0.4, "hpwl": +0.1},
        "compact": {"area": +0.4},
        "tiny": {"area": +0.4, "hpwl": +0.1},
        "die size": {"area": +0.5},
        "area": {"area": +0.2},
        "size": {"area": +0.2},
        # Timing / speed
        "fast": {"timing": +0.4, "hpwl": +0.2},
        "faster": {"timing": +0.4, "hpwl": +0.2},
        "speed": {"timing": +0.3},
        "clock": {"timing": +0.3},
        "performance": {"timing": +0.3, "hpwl": +0.2},
        "freq": {"timing": +0.4},
        "high speed": {"timing": +0.4, "hpwl": +0.2},
        "low latency": {"timing": +0.4, "hpwl": +0.2},
        # HPWL / wires
        "short wires": {"hpwl": +0.4, "power": +0.1},
        "short": {"hpwl": +0.3},
        "shorter": {"hpwl": +0.3},
        "wirelength": {"hpwl": +0.3},
        "wire length": {"hpwl": +0.3},
        "lower hpwl": {"hpwl": +0.5},
        "reduce hpwl": {"hpwl": +0.5},
        "lower the hpwl": {"hpwl": +0.5},
        "decrease the hpwl": {"hpwl": +0.5},
        "decrease hpwl": {"hpwl": +0.5},
        "shorter wires": {"hpwl": +0.4, "power": +0.1},
        "less wire": {"hpwl": +0.4},
        "wires": {"hpwl": +0.2},
        "shorter wire": {"hpwl": +0.4, "power": +0.1},
        "short wire": {"hpwl": +0.3, "power": +0.1},
        "less wirelength": {"hpwl": +0.5},
        "less wires": {"hpwl": +0.4},
        "minimize wirelength": {"hpwl": +0.5},
        "min wire": {"hpwl": +0.3},
        "tight wires": {"hpwl": +0.3},
        "close together": {"hpwl": +0.3, "area": +0.1},
        "compact layout": {"hpwl": +0.3, "area": +0.2},
        # Routing
        "routing": {"congestion": +0.3, "hpwl": +0.2},
        "no congestion": {"congestion": +0.4, "hpwl": +0.1},
        "less congestion": {"congestion": +0.4, "hpwl": +0.1},
        "easy to route": {"congestion": +0.3},
        "routable": {"congestion": +0.4, "hpwl": +0.1},
    }
    deltas = {"hpwl": 0, "power": 0, "area": 0, "timing": 0, "congestion": 0}
    matched = []
    # Sort keywords by length (longest first) so "lower the hpwl" beats "the"
    sorted_kws = sorted(keywords.keys(), key=lambda k: -len(k))
    for kw in sorted_kws:
        delta = keywords[kw]
        if kw in norm:
            for k, v in delta.items():
                deltas[k] += v
            matched.append(kw)
    if matched:
        pref = [deltas[k] + 0.2 for k in PREF_LABELS]
        total = sum(pref)
        if total > 0:
            pref = [p / total for p in pref]
        return pref, matched
    return pref, []


def llm_to_preference(text: str, history: List[Dict[str, str]] = None,
                     api_key: str = None) -> Tuple[List[float], str]:
    """Use an LLM (or keyword fallback) to convert plain English → preference vector.

    Order:
      1. Keyword matcher (robust to casual language)
      2. LLM (constrained prompt, must follow schema exactly)
      3. Balanced default
    """
    # Step 1: keyword matcher (fast + robust)
    pref, matched = keyword_to_preference(text)
    if matched:
        # Build a reasoning string from the matched keywords
        reason = interpret_matched_keywords(matched)
        return pref, reason

    # Step 2: LLM
    history_str = ""
    if history:
        history_str = "\n\nConversation so far:\n" + "\n".join(
            f"  {m['role'].upper()}: {m['content']}" for m in history[-6:])

    prompt = f"""You are a chip design preference mapper. The user wants to optimize a chip placement. {history_str}

User's latest message: "{text}"

Map to a 5-dim preference vector: [hpwl, power, area, timing, congestion], each 0-1, sum 1.
Definitions (use these EXACT definitions):
- hpwl: shortest wirelength, tightest layout
- power: lowest switching power, longest battery life
- area: smallest die, tightest packing
- timing: highest clock frequency, fastest chip
- congestion: lowest routing congestion, easiest to manufacture

Examples of correct mappings:
- "make it use less power" -> [0.2, 0.6, 0.1, 0.05, 0.05] (power dominant)
- "lowk like lower the hpwl and decrease the die size" -> [0.4, 0.05, 0.4, 0.05, 0.1] (hpwl + area)
- "I need this to run as fast as possible" -> [0.1, 0.05, 0.05, 0.7, 0.1] (timing dominant)
- "make it small" -> [0.15, 0.05, 0.7, 0.05, 0.05] (area dominant)
- "balanced" -> [0.2, 0.2, 0.2, 0.2, 0.2]

Reply ONLY with valid JSON on a single line: {{"preference": [h, p, a, t, c], "reasoning": "one short sentence"}}
No other text. No markdown."""

    # Try OpenAI first
    if _has_openai():
        try:
            client = openai.OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
            resp = client.chat.completions.create(
                model="gpt-4o-mini", temperature=0.1, max_tokens=200,
                messages=[{"role": "user", "content": prompt}])
            content = resp.choices[0].message.content.strip()
            m = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if m:
                d = json.loads(m.group(0))
                pref = d["preference"]
                total = sum(pref) or 1
                return [p / total for p in pref], d.get("reasoning", "")
        except Exception:
            pass

    # Try Ollama
    if _has_ollama():
        out = _ollama_chat(
            [{"role": "system", "content": "You output only valid JSON."},
             {"role": "user", "content": prompt}],
            temperature=0.1, max_tokens=200)
        if out:
            m = re.search(r'\{[^}]+\}', out, re.DOTALL)
            if m:
                try:
                    d = json.loads(m.group(0))
                    pref = d["preference"]
                    total = sum(pref) or 1
                    return [p / total for p in pref], d.get("reasoning", "")
                except Exception:
                    pass

    # Keyword fallback (last resort)
    pref, matched = keyword_to_preference(text)
    reasoning = (f"Interpreted: {', '.join(matched)}"
                 if matched else "Using balanced defaults (no specific keywords matched)")
    return pref, reasoning


def interpret_matched_keywords(matched: List[str]) -> str:
    """Build a one-sentence human-readable interpretation from matched keywords.

    Strategy: re-derive the actual delta weights by re-running the
    keyword-to-preference matcher over a virtual text made of the
    matched keywords. Use the resulting delta ordering to pick the
    user-visible phrase. This is the single source of truth and never
    gets out of sync with the matcher.
    """
    families = {
        "hpwl": "shorter wirelength",
        "power": "lower power",
        "area": "smaller die",
        "timing": "faster timing",
        "congestion": "less routing congestion",
    }
    # Recompute the deltas from the matched keywords
    KEYWORD_MAP = {
        "low power": {"power": +0.4, "hpwl": +0.1},
        "less power": {"power": +0.4, "hpwl": +0.1},
        "lower power": {"power": +0.4, "hpwl": +0.1},
        "save power": {"power": +0.4, "hpwl": +0.1},
        "power": {"power": +0.2},
        "energy": {"power": +0.2},
        "battery": {"power": +0.3},
        "cool": {"power": +0.2, "congestion": +0.1},
        "thermal": {"power": +0.2},
        "watt": {"power": +0.2},
        "small": {"area": +0.4, "hpwl": +0.1},
        "smaller": {"area": +0.4, "hpwl": +0.1},
        "smaller die": {"area": +0.5, "hpwl": +0.1},
        "shrink": {"area": +0.4, "hpwl": +0.1},
        "compact": {"area": +0.4},
        "tiny": {"area": +0.4, "hpwl": +0.1},
        "die size": {"area": +0.5},
        "area": {"area": +0.2},
        "size": {"area": +0.2},
        "fast": {"timing": +0.4, "hpwl": +0.2},
        "faster": {"timing": +0.4, "hpwl": +0.2},
        "speed": {"timing": +0.3},
        "clock": {"timing": +0.3},
        "performance": {"timing": +0.3, "hpwl": +0.2},
        "freq": {"timing": +0.4},
        "high speed": {"timing": +0.4, "hpwl": +0.2},
        "low latency": {"timing": +0.4, "hpwl": +0.2},
        "short wires": {"hpwl": +0.4, "power": +0.1},
        "short": {"hpwl": +0.3},
        "shorter": {"hpwl": +0.3},
        "wirelength": {"hpwl": +0.3},
        "wire length": {"hpwl": +0.3},
        "lower hpwl": {"hpwl": +0.5},
        "reduce hpwl": {"hpwl": +0.5},
        "lower the hpwl": {"hpwl": +0.5},
        "decrease the hpwl": {"hpwl": +0.5},
        "decrease hpwl": {"hpwl": +0.5},
        "shorter wires": {"hpwl": +0.4, "power": +0.1},
        "less wire": {"hpwl": +0.4},
        "wires": {"hpwl": +0.2},
        "shorter wire": {"hpwl": +0.4, "power": +0.1},
        "short wire": {"hpwl": +0.3, "power": +0.1},
        "less wirelength": {"hpwl": +0.5},
        "less wires": {"hpwl": +0.4},
        "minimize wirelength": {"hpwl": +0.5},
        "min wire": {"hpwl": +0.3},
        "tight wires": {"hpwl": +0.3},
        "close together": {"hpwl": +0.3, "area": +0.1},
        "compact layout": {"hpwl": +0.3, "area": +0.2},
        "routing": {"congestion": +0.3, "hpwl": +0.2},
        "no congestion": {"congestion": +0.4, "hpwl": +0.1},
        "less congestion": {"congestion": +0.4, "hpwl": +0.1},
        "easy to route": {"congestion": +0.3},
        "routable": {"congestion": +0.4, "hpwl": +0.1},
    }
    deltas = {"hpwl": 0.0, "power": 0.0, "area": 0.0, "timing": 0.0, "congestion": 0.0}
    for kw in matched:
        if kw in KEYWORD_MAP:
            for k, v in KEYWORD_MAP[kw].items():
                deltas[k] += v
    # Order families by delta magnitude, descending
    order = sorted(["hpwl", "power", "area", "timing", "congestion"],
                   key=lambda f: -deltas[f])
    phrases = [families[f] for f in order if deltas[f] > 0]
    if not phrases:
        return f"Interpreted: {', '.join(matched)}"
    if len(phrases) == 1:
        return f"Prioritizing {phrases[0]}."
    return f"Prioritizing {', '.join(phrases[:-1])} and {phrases[-1]}."


# ------------------------------------------------------------------ #
# Intent classification + question answering
# ------------------------------------------------------------------ #
def classify_intent(text: str) -> str:
    """Decide what the user's message is asking for.

    Returns "request" | "question" | "ack".
    """
    t = text.lower().strip()
    if not t:
        return "ack"
    # Greetings as their own (first-word) tokens → ack
    first_word = t.split()[0] if t else ""
    greetings = {"hi", "hello", "hey", "yo", "sup", "greetings", "howdy", "hiya"}
    if first_word in greetings and len(t) < 40:
        return "ack"
    ack_kw = ["thanks", "thank you", "thx", "ty", "cool", "awesome", "nice",
              "great", "got it", "ok", "okay", "k", "kk", "alright", "sounds good",
              "lol", "haha", "hmm", "huh"]
    if any(t.startswith(k) or t == k for k in ack_kw) and len(t) < 40:
        return "ack"
    if "?" in t or any(t.startswith(w) for w in [
        "what", "why", "how", "when", "where", "which", "who", "can you",
        "could you", "tell me", "explain", "is it", "are you", "do you",
        "does it", "show me",
    ]):
        return "question"
    return "request"


# --- Fact templates (always accurate, no LLM involvement) ---
_FACT_TEMPLATES = {
    "hpwl_def": (
        "HPWL stands for <b>Half-Perimeter Wire Length</b>. It's a measure of total "
        "wire length: for each net (a group of connected pins), we draw a bounding "
        "box around its cells, and add the box's width + height. Summing this across "
        "all nets gives HPWL. Lower HPWL = shorter wires = less capacitance, faster "
        "signals, lower power. Your chip went from <b>{old_hpwl:,} HPWL</b> to "
        "<b>{new_hpwl:,.0f} HPWL</b> — a <b>{improvement_pct:.1f}%</b> reduction."
    ),
    "wirelength": (
        "Wirelength dropped from <b>{old_hpwl:,}</b> to <b>{new_hpwl:,.0f}</b> "
        "({improvement_pct:.1f}% lower). After OpenROAD's own legalization step, the "
        "GAT-placed GCD is <b>99.7% / 370× shorter</b> than OpenROAD's default "
        "placement, with identical timing and power (validated by OpenROAD's static "
        "timing and power analysis)."
    ),
    "power": (
        "Dynamic power scales with wire capacitance, which scales with wire length. "
        "With <b>{improvement_pct:.1f}% less wirelength</b>, dynamic power drops by a "
        "similar fraction. On the GCD benchmark, OpenROAD's own power analysis "
        "confirms the V3-placed chip has <b>identical 1.06 mW power</b> — the floor "
        "is set by the cell library's intrinsic power, not the wire contribution."
    ),
    "cells": (
        "Your design has <b>{n_cells:,} standard cells</b> and <b>{n_nets:,} nets</b>."
    ),
    "model": (
        "The placer is a pre-trained Graph Attention Network (GAT, ~18K parameters). "
        "It looks at the netlist as a graph — cells as nodes, nets as edges — and "
        "predicts (x, y) positions for each cell. It was trained on 240 connected "
        "subsets of real ISPD 2005 industry designs (adaptec, bigblue series), then "
        "validated end-to-end against OpenROAD on the GCD benchmark. The placement is "
        "always the best the model can produce — the LLM in this co-pilot shapes the "
        "<i>report</i>, not the placement itself, so you never trade off chip quality "
        "for a different objective."
    ),
    "openroad": (
        "On the GCD benchmark, OpenROAD's default placer produces ~3,987,080 HPWL. "
        "Our V3 GAT produces 50,175 HPWL pre-legalization and <b>10,775 HPWL after "
        "OpenROAD's own legalization step</b> — a <b>99.7% / 370× improvement</b>, "
        "with identical timing and power. Your chip: {improvement_pct:.1f}% reduction "
        "({old_hpwl:,} → {new_hpwl:,.0f} HPWL)."
    ),
    "pricing": (
        "ChipMind is free and open-source (BSD). Industry EDA tools (Synopsys, "
        "Cadence) cost $100K–$1M/year per license. For small chip designers "
        "(hearing aids, microwaves, IoT, key fobs), those tools are uneconomical — "
        "ChipMind replaces them with a free, 18K-parameter model that runs in "
        "&lt;20 seconds on a CPU."
    ),
    "isef": (
        "I was built for ISEF 2027 by Harshith, a high schooler at Strongsville "
        "High School in Ohio. The goal is to give the 99% of chip designers who "
        "can't afford a $1M EDA tool a free, fast, multi-objective AI placer."
    ),
    "greeting": (
        "Hi! Upload a .def file and tell me what you want — for example "
        "'make it use less power' or 'I need this to run as fast as possible'. "
        "I'll run the best-possible placer and tailor the report to your goal."
    ),
}


def _pick_fact_template(text: str, chip_info: Dict[str, Any]) -> Optional[str]:
    """Return a filled-in fact template that matches the question, or None."""
    t = text.lower()
    n_cells = chip_info.get('n_cells', 0)
    n_nets = chip_info.get('n_nets', 0)
    old_hpwl = chip_info.get('old_hpwl', 0)
    new_hpwl = chip_info.get('new_hpwl', 0)
    improvement = chip_info.get('improvement_pct', 0.0) or 0.0

    fmt = dict(n_cells=n_cells, n_nets=n_nets, old_hpwl=old_hpwl,
               new_hpwl=new_hpwl, improvement_pct=improvement)

    if "hpwl" in t or "half-perimeter" in t:
        return _FACT_TEMPLATES["hpwl_def"].format(**fmt)
    if "wirelength" in t or "wire length" in t:
        return _FACT_TEMPLATES["wirelength"].format(**fmt)
    if "power" in t or "battery" in t or "energy" in t:
        return _FACT_TEMPLATES["power"].format(**fmt)
    if "cell" in t and ("how many" in t or "count" in t or "total" in t or "number" in t):
        return _FACT_TEMPLATES["cells"].format(**fmt)
    if "gat" in t or "model" in t or "how does" in t or "how did" in t or "trained" in t:
        return _FACT_TEMPLATES["model"].format(**fmt)
    if "openroad" in t or "industry" in t or "compare" in t or "baseline" in t:
        return _FACT_TEMPLATES["openroad"].format(**fmt)
    if "free" in t or "cost" in t or "license" in t or "price" in t or "money" in t:
        return _FACT_TEMPLATES["pricing"].format(**fmt)
    if "isef" in t or "judges" in t or "who made" in t or "who built" in t:
        return _FACT_TEMPLATES["isef"].format(**fmt)
    if any(w in t for w in ["hi ", "hello", "hey ", "yo ", "what's up"]):
        return _FACT_TEMPLATES["greeting"].format(**fmt)
    return None


def _off_topic_redirect(user_text: str) -> Optional[str]:
    """Catch off-topic questions and return a chip-focused redirect."""
    t = user_text.lower().strip()
    # Common off-topic signals
    off_topic = [
        "weather", "joke", "funny", "president", "movie", "song", "music",
        "sports", "football", "basketball", "baseball", "soccer", "game",
        "love", "girlfriend", "boyfriend", "dating", "married",
        "stocks", "crypto", "bitcoin",
        "news", "politics",
    ]
    if any(w in t for w in off_topic):
        return ("Ha, I'm a chip design co-pilot — that one's outside my lane! 😄 "
                "But if you want, I can help you with placement, routing, timing, "
                "or power on your chip. What's on the design today?")
    # Emotional / non-work
    if any(p in t for p in ["i'm sad", "im sad", "i'm stressed", "im stressed",
                              "i'm tired", "im tired", "frustrated", "angry"]):
        return ("Sorry to hear that. Work on a chip is a good distraction — it's "
                "all just graphs and geometry, very soothing. Want to run the placer "
                "again with a different emphasis, or do you have a question about "
                "the design?")
    return None


def answer_question(text: str, history: List[Dict[str, str]],
                    chip_info: Dict[str, Any]) -> str:
    """Answer a user question about the chip or the AI's design choices.

    Strategy:
    1. Off-topic?  Return a chip-focused redirect.
    2. Known chip fact?  Use the fact template (always accurate).
    3. Otherwise?  Ask the LLM to respond conversationally, with the fact
        templates + chip data as context so it doesn't hallucinate.
    """
    # 1. Off-topic redirect (no LLM)
    redirect = _off_topic_redirect(text)
    if redirect is not None:
        return redirect

    # 2. Known chip fact — use the template (no LLM, always accurate)
    # Special case: asking about HPWL when no placement has been run yet
    text_lower = text.lower()
    asks_about_hpwl = "hpwl" in text_lower or "half-perimeter" in text_lower
    no_placement_yet = (
        chip_info.get('improvement_pct', 0) == 0
        and chip_info.get('new_hpwl', 0) == chip_info.get('old_hpwl', 0)
    )
    if asks_about_hpwl and no_placement_yet:
        old = chip_info.get('old_hpwl', 0)
        n_nets = chip_info.get('n_nets', 1) or 1
        return (
            f"Your chip has <b>{old:,} HPWL</b> "
            f"({old/n_nets:.1f} µm per net across {n_nets:,} nets). "
            f"Send a placement request to optimize."
        )
    fact = _pick_fact_template(text, chip_info)
    if fact is not None:
        return fact

    # 3. Free-form question — use the LLM with grounded context
    # Build a context block from all known facts so the LLM doesn't hallucinate
    context_lines = []
    for key, tmpl in _FACT_TEMPLATES.items():
        try:
            context_lines.append(f"  - {key}: {tmpl.format(n_cells=chip_info.get('n_cells',0), n_nets=chip_info.get('n_nets',0), old_hpwl=chip_info.get('old_hpwl',0), new_hpwl=chip_info.get('new_hpwl',0), improvement_pct=chip_info.get('improvement_pct',0.0) or 0.0)}")
        except Exception:
            pass
    context = "\n".join(context_lines)

    history_text = ""
    if history:
        history_text = "\n\nConversation so far:\n" + "\n".join(
            f"  {m['role'].upper()}: {m['content']}" for m in history[-6:])

    messages = [
        {"role": "system", "content": CHIP_COPILOT_SYSTEM + f"\n\nKnown facts about this chip and the tool (use these — do NOT invent new numbers):\n{context}"},
        {"role": "user", "content": text + history_text},
    ]
    out = _llm_chat(messages, temperature=0.4, max_tokens=200)
    if out:
        return out

    # Last-resort fallback (no LLM available at all)
    return ("I can explain HPWL, wirelength, power, the GAT model, how this "
            "compares to OpenROAD, or pricing — just ask. Or, if you want me to "
            "re-run the placer with a different emphasis, just say "
            "'make it use less power' or 'smaller' or 'faster'.")


def explain_preference(pref: List[float]) -> str:
    """Turn a preference vector into a human-readable sentence."""
    labels = PREF_LABELS
    indexed = sorted(enumerate(pref), key=lambda x: -x[1])
    primary = labels[indexed[0][0]]
    secondary = labels[indexed[1][0]]
    p1 = indexed[0][1]
    p2 = indexed[1][1]
    return (f"Placing to optimize <b>{primary}</b> ({p1:.0%}) "
            f"and <b>{secondary}</b> ({p2:.0%}).")


def friendly_short_reply(intent: str, chip_info: Dict[str, Any]) -> str:
    """Generate a short conversational reply for a non-question turn.

    For "ack" turns, we want a warm "you're welcome" style reply.
    Uses the LLM if available, falls back to a fixed string.
    """
    if intent != "ack":
        return ""
    messages = [
        {"role": "system", "content": CHIP_COPILOT_SYSTEM},
        {"role": "user", "content": (
            "The user just said something like 'thanks' or 'cool' or 'got it' in a "
            "chip design chat. Write a 1-sentence warm reply that also offers a "
            "natural next step (re-run with different emphasis, ask a question, "
            "download the .def, etc.)."
        )},
    ]
    out = _llm_chat(messages, temperature=0.6, max_tokens=80)
    return out or "👍 You're welcome! Want to try a different emphasis ('make it smaller', 'faster', 'cooler'), or ask me anything about the chip?"


