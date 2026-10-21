#!/usr/bin/env python3
"""
Scores the five criteria in criteria.md, one try per scenario, and writes
results/run_<stamp>_<label>.md.

    python score_eval.py --label before
    python score_eval.py --label after

Reuses run_eval.run_once (caching off, trace captured). The PASS/FAIL rules
below are copied from the wording of criteria.md, so change them only if the
criterion is revised there first.
"""

import argparse
import datetime as dt
import re

import config
import scenarios as sc
import run_eval
import agent as agent_module

config.CACHE_ENABLED = False


def instrumented_run(scenario):
    """run_once, plus a record of which items reached each tool."""
    calls = {"suggest_outfit": [], "create_fit_card": []}
    real_outfit, real_card = agent_module.suggest_outfit, agent_module.create_fit_card

    def outfit(item, wardrobe):
        calls["suggest_outfit"].append(item["id"])
        return real_outfit(item, wardrobe)

    def card(text, item):
        calls["create_fit_card"].append(item["id"])
        return real_card(text, item)

    agent_module.suggest_outfit, agent_module.create_fit_card = outfit, card
    try:
        record = run_eval.run_once(scenario)
    finally:
        agent_module.suggest_outfit, agent_module.create_fit_card = real_outfit, real_card
    record["calls"] = calls
    return record


def sentences(text):
    return [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p]


def first_words(text, n=5):
    return " ".join(re.findall(r"[a-z0-9']+", text.lower())[:n])


def has_price(card, price):
    return re.search(rf"\$\s?{int(round(price))}(?:\.0+)?(?!\d)", card) is not None


def check_c1(rec):
    s = rec["session"] or {}
    ok = (not rec["crashed"] and not s.get("error") and bool(s.get("outfit_suggestion"))
          and bool((s.get("fit_card") or "").strip()))
    return ok, "fit card returned" if ok else f"stopped/failed: {rec['crashed'] or s.get('error')}"


def check_c2(rec):
    s = rec["session"] or {}
    stopped = bool(s.get("error")) and not rec["calls"]["suggest_outfit"] \
        and s.get("fit_card") is None and s.get("outfit_suggestion") is None
    return stopped, ("stopped before suggest_outfit: " + str(s.get("error"))[:80]) if stopped \
        else f"did not stop cleanly (error={s.get('error')!r}, suggest_outfit calls={rec['calls']['suggest_outfit']})"


def check_c3(rec):
    s = rec["session"] or {}
    if not s.get("selected_item"):
        return False, f"no item selected ({s.get('error')})"
    top = s["search_results"][0]["id"]
    sel = s["selected_item"]["id"]
    got = rec["calls"]
    ok = sel == top and got["suggest_outfit"] == [sel] and got["create_fit_card"] == [sel]
    return ok, f"top={top} selected={sel} suggest_outfit got={got['suggest_outfit']} create_fit_card got={got['create_fit_card']}"


def check_c4_single(rec):
    s = rec["session"] or {}
    card, item = (s.get("fit_card") or ""), s.get("selected_item")
    if not card or not item:
        return False, "no fit card"
    n = len(sentences(card))
    parts = {"2-4 sentences": 2 <= n <= 4, "price": has_price(card, item["price"]),
             "platform": item["platform"].lower() in card.lower()}
    bad = [k for k, v in parts.items() if not v]
    return not bad, "ok" if not bad else f"missing: {', '.join(bad)} ({n} sentences)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    by_c = {c: [x for x in sc.SCENARIOS if x["criterion"] == c] for c in (1, 2, 3, 4)}
    results = {}  # criterion -> list of (ok, note, record, scenario)
    for c, checker in ((1, check_c1), (2, check_c2), (3, check_c3), (4, check_c4_single)):
        results[c] = []
        for scenario in by_c[c]:
            print(f"[c{c}] {scenario['query']}", flush=True)
            rec = instrumented_run(scenario)
            ok, note = checker(rec)
            results[c].append([ok, note, rec, scenario])

    # criterion 4: first-five-words must also be unique across the five cards
    firsts = [first_words((r[2]["session"] or {}).get("fit_card") or "") for r in results[4]]
    for i, r in enumerate(results[4]):
        if r[0] and firsts.count(firsts[i]) > 1:
            r[0], r[1] = False, f"opening shared with another card: '{firsts[i]}'"

    # criterion 5: search output only, through MCP, 2 queries per try
    from mcp_client import call_tool
    c5 = []
    for desc, size, price in sc.CRITERION_5_QUERIES:
        res = call_tool("search_listings", {"description": desc, "size": size, "max_price": price})
        over = [r["id"] for r in res if price is not None and r["price"] > price]
        wrong = [r["id"] for r in res if size and not run_eval_size_ok(size, r["size"])]
        c5.append((not over and not wrong, f"{desc!r} size={size} max={price}: {len(res)} results, over-price={over}, wrong-size={wrong}"))
    c5_tries = [(c5[2 * i][0] and c5[2 * i + 1][0], c5[2 * i][1] + "\n  " + c5[2 * i + 1][1]) for i in range(5)]

    targets = {1: 4, 2: 5, 3: 5, 4: 4, 5: 10}
    names = {1: "1. Matching query completes all three tools", 2: "2. Impossible query stops before suggest_outfit",
             3: "3. Selected item is the item that reached the tools", 4: "4. Fit card: 2-4 sentences, price, platform, distinct opening",
             5: "5. Price ceiling and size respected"}
    rows = []
    for c in (1, 2, 3, 4):
        marks = [r[0] for r in results[c]]
        rows.append((c, f"{targets[c]} of 5", marks))
    rows.append((5, "10 of 10", [t[0] for t in c5_tries]))

    lines = [f"# Run log — {args.label}", "",
             f"- Produced by: `score_eval.py` (reuses `run_eval.run_once`, caching off, temperature {config.TEMPERATURE})",
             f"- When: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", "",
             "| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |", "|---|---|---|---|---|---|---|---|"]
    for c, target, marks in rows:
        passes = sum(marks) if c != 5 else sum(x[0] for x in c5)
        total = 5 if c != 5 else 10
        need = int(target.split()[0])
        verdict = ("MET" if passes >= need else "MISSED") + f" ({passes}/{total})"
        lines.append(f"| {names[c]} | {target} | " + " | ".join("PASS" if m else "FAIL" for m in marks) + f" | {verdict} |")
    lines += ["", "Criterion 5: each try covers two queries (both must pass); 10 queries in all.", "", "---", "", "## Detail", ""]
    for c in (1, 2, 3, 4):
        lines.append(f"### Criterion {c}")
        for i, (ok, note, rec, scenario) in enumerate(results[c], 1):
            s = rec["session"] or {}
            lines += ["", f"**Try {i}: {'PASS' if ok else 'FAIL'}** — `{scenario['query']}` — {note}", ""]
            if rec["crashed"]:
                lines += ["```", rec["crashed"], "```"]
            elif s.get("fit_card"):
                lines += ["```", f"{(s['selected_item'] or {}).get('title')} (${(s['selected_item'] or {}).get('price')}, {(s['selected_item'] or {}).get('platform')})", s["fit_card"], "```"]
            if rec["trace"]:
                lines += ["Trace:", "```", rec["trace"], "```"]
    lines += ["", "### Criterion 5", ""]
    for i, (ok, note) in enumerate(c5_tries, 1):
        lines += [f"**Try {i}: {'PASS' if ok else 'FAIL'}**", "```", note, "```"]

    config.RESULTS_DIR.mkdir(exist_ok=True)
    path = config.RESULTS_DIR / f"run_{dt.datetime.now().strftime('%Y-%m-%d_%H%M')}_{args.label}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:14]))
    print(f"\nWrote {path}")


def run_eval_size_ok(wanted, listed):
    """Independent of tools.py: whole-word match, or a One Size listing."""
    words = set(re.split(r"[^a-z0-9]+", listed.lower()))
    return {"one", "size"} <= words or all(w in words for w in re.split(r"[^a-z0-9]+", wanted.lower()) if w)


if __name__ == "__main__":
    main()
