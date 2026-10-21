# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

A user types a plain-language request such as "vintage graphic tee under $30, size M"
and, optionally, supplies the clothes they already own. FitFindr searches 40 thrift
listings, picks the best match, suggests one or two outfits that combine it with the
user's wardrobe (or general styling advice if the wardrobe is empty), and writes a
short social-media style fit card about the find. If nothing matches, it stops early
and says what to change (price, size or keywords) instead of calling the model.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 listings by price ceiling and size, scores the rest by keyword overlap with the description, and returns the best matches.
- **Inputs:** `description` (str), `size` (str or None), `max_price` (float or None, inclusive).
- **Returns:** A list of at most `config.SEARCH_RESULT_LIMIT` (10) listing dicts, best match first. Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`. A listing must match at least half of the description's keywords (added in unit 4). Size is a whole-word match (`M` matches `S/M` and `M/L`, never `XL` or `US 9`; `One Size` matches anything).
- **When it has nothing:** An empty list `[]` (never None, never an exception).

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the chosen item and the user's wardrobe.
- **Inputs:** `new_item` (dict, a listing), `wardrobe` (dict with an `items` list of dicts having `name`, `category`, `colors`, `style_tags`, `notes`).
- **Returns:** A non-empty str of outfit suggestions that name owned pieces.
- **When it has nothing:** If `wardrobe["items"]` is empty it returns general styling advice (still a non-empty str). If the model returns blank text it returns a fixed fallback sentence.

### `create_fit_card`

- **What it does:** Asks the model for a casual 2-4 sentence caption about the find that mentions the item, its price and its platform.
- **Inputs:** `outfit` (str, from `suggest_outfit`), `new_item` (dict, a listing).
- **Returns:** A str caption of 2-4 sentences.
- **When it has nothing:** If `outfit` is empty or whitespace it returns the str "No outfit suggestion was provided, so there is nothing to write a fit card about." without calling the model.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that names what to change (raise the price limit, drop or change the size, use simpler keywords) and return the session without calling `suggest_outfit` or `create_fit_card`. Otherwise store the first result in `session["selected_item"]` and go on to `suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex (`agent.py::parse_query`), no model call. It pulls a price ceiling from "under/below/max/up to $N" or a bare "$N", a size from "size X", and treats the rest as the description.

**What moves through the session:** `query` -> `parsed` -> `search_results` -> `selected_item` -> `outfit_suggestion` -> `fit_card`. Each tool's result is written into the session and the next tool reads its input back out of it. `error` is set only when the run stops early.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

The empty-search path (no key needed):

```
$ python app.py ask 'designer ballgown size XXS under $5'

  Nothing matched 'designer ballgown'. Try to raise the price limit above $5, drop or change the size (XXS), or use simpler keywords such as 'tee', 'jeans' or 'jacket'.

0 model calls this session
```

The happy path:

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   Outfit 1: Pair the graphic tee with baggy straight-leg jeans, black combat boots, and the black crossbody bag. Layer the vintage black denim jacket on top and finish with the brown leather belt.

Outfit 2: Tuck the graphic tee into the wide-leg khaki trousers, add the black combat boots and brown leather belt, and layer the black cropped zip hoodie open over top.

  Fit card: Still shaking that I manifested this 2003 tour bootleg tee on depop for only $24. The fade on it is literally insane and gives off the exact beat-up rockstar vibe I’ve been hunting for. Going to throw it on with baggy straight-leg jeans and combat boots today, but honestly it's gonna look so good tucked into wide-leg khakis later this week too.

2 model calls this session, 431 prompt + 165 output tokens
```

State check on the same query: `session["selected_item"]["id"]` = `lst_006`, `session["search_results"][0]["id"]` = `lst_006`, `session["error"]` = `None`.

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; r=search_listings('graphic tee', max_price=30); print([(x['id'],x['title'],x['price']) for x in r])"
[('lst_006', 'Graphic Tee — 2003 Tour Bootleg Style', 24.0), ('lst_002', 'Y2K Baby Tee — Butterfly Print', 18.0), ('lst_033', 'Vintage Band Tee — Faded Grey', 19.0), ('lst_015', 'Vintage Graphic Hoodie — Faded Black', 26.0), ('lst_017', 'Mesh Long-Sleeve Top — Black', 15.0), ('lst_012', 'Oversized Crewneck Sweatshirt — Vintage Navy', 20.0), ('lst_011', 'Low-Rise Cargo Pants — Khaki', 27.0)]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit 1: Pair the Vintage Levi's 501 Jeans with the White ribbed tank top, the Vintage black denim jacket, and the Chunky white sneakers. Add the Brown leather belt to finish the look.

Outfit 2: Wear the Vintage Levi's 501 Jeans under the Oversized grey crewneck sweatshirt, paired with the Black combat boots and the Brown leather belt. Throw on the Black crossbody bag to complete your outfit.
```

Empty wardrobe (`get_empty_wardrobe()`) returns general advice instead of failing:

```
Tuck a cropped white graphic tee into the jeans, layer an oversized black leather jacket over top, and finish the look with classic black Converse or chunky platform loafers.

Alternatively, pair them with an oversized neutral beige crewneck sweater, a worn-in brown leather belt, and retro white running sneakers like New Balance.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Still not over finding these vintage Levi's 501 jeans in the absolute best medium wash on depop. For only $38, they have that perfectly worn-in slouch that usually takes years to break in. Can’t wait to live in these with just a simple pair of white sneakers all season.
```

Three runs on the same item with `AI201_CACHE=0` came out different each time:

```
- Still riding the high from finding these vintage Levi's 501 jeans on depop for just $38. The medium wash has that exact 90s slouch I've been hunting for. Can't wait to live in these with my favorite white sneakers all spring.
- Found these vintage Levi's 501 jeans on depop for only $38 and I am literally never taking them off. They have the absolute best medium wash and worn-in feel. Just need to style them with my favorite white sneakers and I'm good to go.
- Still recovering from the fact that I found these vintage Levi's 501 jeans on depop for just $38. The medium wash is *so* broken-in and has that exact 90s slouch I've been hunting for. Honestly just gonna live in these with my favorite white sneakers from now on.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* Claude to set up the project: create the venv and install `requirements.txt`.
- *What came back:* It created the venv with the system `python3`, which is 3.14.2. The install worked, but `requirements.txt` says 3.14 is unsupported.
- *What I changed:* I deleted the venv and rebuilt it with Python 3.13 (`/opt/homebrew/bin/python3.13`), then reinstalled.

**Moment 2**

- *What I asked for:* Claude to build `search_listings` following the starter's TODO (keyword overlap, filter on size and price).
- *What came back:* A plain keyword scorer. The data has sizes like `S/M`, `W30 L30`, `US 9` and `XL (oversized)`, so a substring size test would match `"s"` inside `"us 9"`.
- *What I changed:* I replaced the substring test with a whole-word comparison (`_size_matches`), made `One Size` listings match any size, and made criterion 5 check this directly.

**Moment 3 (unit 4)**

- *What I asked for:* Claude to write a scorer (`score_eval.py`) that turns the wording of my five criteria into PASS/FAIL checks.
- *What came back:* A scorer whose criterion 5 check first reused `tools._size_matches` to judge the search results, so the tool would have been grading itself.
- *What I changed:* I rewrote that check inside the scorer so it doesn't import anything from `tools.py`.

**Moment 4 (unit 4)**

- *What I asked for:* Claude to diagnose the criterion 2 miss and propose one change.
- *What came back:* A diagnosis pointing at `search_listings` (any single keyword hit counts) rather than at the loop's branch, and a fix requiring at least half the keywords to match. It predicted the fix would break the vague "summer picnic" query before I ran it.
- *What I changed:* I kept the fix and ran the full test again anyway. The prediction held: criterion 2 went to 5/5 and criterion 1 dropped to 4/5. I reported the trade instead of loosening the target or revising the criterion.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log: Before

How the tries were run: `python score_eval.py --label before` (full output in `results/run_2026-10-21_0850_before.md`). It reuses `run_eval.run_once` with the cache off and temperature 0.9, but I wrote it instead of using `run_eval.py` directly because `run_eval.py` repeats every scenario five times and leaves the verdicts blank. Here the PASS/FAIL rules are coded straight from the wording of `criteria.md`. For criteria 1 to 4, one try is one run of one query, and five queries make five tries, as the criteria are worded ("5 queries", "5 different items"). Criterion 5 names 10 queries and checks only search output, so it goes through the MCP search tool with no model call, two queries per try column (both must pass), 10 of 10 overall.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before suggest_outfit | 5 of 5 | PASS | PASS | FAIL | PASS | PASS | MISSED (4/5) |
| 3. Selected item is the item that reached the tools | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2-4 sentences, price, platform, distinct opening | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling and size respected | 10 of 10 | PASS | PASS | PASS | PASS | PASS | MET (10/10) |

**Real output from one try**: the criterion 2 miss (Try 3), produced by `agent.py::run_agent` calling `tools.py::search_listings` through MCP:

```
Try 3: FAIL: `white leather wedding dress` did not stop cleanly (error=None, suggest_outfit calls=['lst_022'])

90s Leather Bomber — Black ($75.0, depop)
Still can't believe I found this holy grail 90s Leather Bomber — Black scrolling on depop for $75. It literally makes any basic outfit look instantly cool, whether I'm throwing it over a white ribbed tank and baggy jeans or a cropped hoodie with khakis. Absolute keeper.

[2] search_listings (via MCP)
      in:  {'description': 'white leather wedding dress', 'size': None, 'max_price': None}
      out: 10 items: 90s Leather Bomber — Black, Leather Belt — Brown, Braided, Low-Top Canvas Sneakers — Off-White … +7 more
[3] select
      out: 90s Leather Bomber — Black ($75.0, depop)
```

And a passing try for criterion 3 (`agent.py::run_agent`, wrapped to record what each tool received):

```
Try 1: PASS: `vintage jeans size W30`: top=lst_001 selected=lst_001 suggest_outfit got=['lst_001'] create_fit_card got=['lst_001']
```

And a passing criterion 4 card (`tools.py::create_fit_card`):

```
Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
Still not over finding this 2003 tour bootleg graphic tee for just $24 on depop—the fade on it is honestly unmatched. Thinking about layering it over a white ribbed tank with wide-leg khakis and chunky sneakers, or keeping it grungy with baggy denim and combat boots.
```

---

## Verdicts and Diagnoses

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4 of 5 | MET (5/5) | All five queries returned a fit card with no error. But see the diagnosis below: one of the five passed on a weak match. |
| 2 | Impossible query stops before suggest_outfit | 5 of 5 | MISSED (4/5) | Target was 5 of 5, and "white leather wedding dress" got through to suggest_outfit. |
| 3 | Selected item is the item that reached the tools | 5 of 5 | MET (5/5) | In all five runs the top result, `selected_item`, and the ids that reached `suggest_outfit` and `create_fit_card` were the same. |
| 4 | Fit card: 2-4 sentences, price, platform, distinct opening | 4 of 5 | MET (5/5) | All five cards passed every check, and no two opened with the same five words. |
| 5 | Price ceiling and size respected | 10 of 10 | MET (10/10) | None of the 10 queries returned anything over its ceiling or in a non-matching size. |

**Diagnoses**

- **Criterion 2 miss: the tool, not the branch.** The branch itself is fine: it fired on 4 of 5 impossible queries and the one-line check `if not results` is correct. The miss happened one step earlier. `search_listings` scores each listing by summing keyword hits and keeps anything above zero, so a single shared word is enough. "white leather wedding dress" shares "leather" with the bomber jacket (and "white" with other items), so the tool returned 10 results for something the data does not have, and the loop correctly went on with them. Mechanism: OR-style keyword matching with a threshold of one hit.
- **Criterion 1 passed for a bad reason in one try.** "something cute for a summer picnic" returned a crochet halter top because "cute" appears in its description. That is the same mechanism as the miss above, and it counted as a pass because my rule for criterion 1 only checks that a fit card came back, not that the item was a sensible match. So the 5/5 in the before table overstates how well search works.
- **Criteria 3 and 5 are deterministic code**, so a 5/5 and 10/10 tells me little; they would only fail if the loop or filter were broken, which is what they exist to catch. **Criterion 4:** I got 5/5 against a target that allowed one miss, so I would call my target on the loose side; I would tighten it to 5 of 5 or add a check that the card mentions something specific to the item (a colour or era), because "price and platform" are handed to the model in the prompt.
- Pattern: both real findings (criterion 2's miss, criterion 1's weak pass) trace to the same place, the `search_listings` scoring threshold, so they are one problem.

I did not revise any criterion in `criteria.md`.

---

## Loop Trace

From `python app.py ask 'vintage graphic tee under $30' --trace` (the run in `results/run_2026-10-21_0850_before.md`, Criterion 1 Try 1). The search step shows `(via MCP)`.

**Happy path**

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey, Vintage Graphic Hoodie — Faded Black … +7 more
[3] select
      out: Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
      →    first result goes into session['selected_item']
[4] suggest_outfit
      in:  Graphic Tee — 2003 Tour Bootleg Style + wardrobe of 10 items
      out: Wear the graphic tee with the baggy straight-leg jeans, black combat boots, and the brown leather belt. Layer …
[5] create_fit_card
      in:  Graphic Tee — 2003 Tour Bootleg Style + outfit text
      out: found this insane 2003 tour bootleg graphic tee on depop for only $24 and my life is officially changed. hones…
```

**Try 2: PASS** — `looking for a y2k top size S` — fit card returned

```
Mesh Long-Sleeve Top — Black ($15.0, depop)
found this black mesh long-sleeve top on depop for just $15 and honestly it’s already doing way too much heavy lifting in my closet. Layering it under an oversized grey crewneck with wide-leg khakis is the lazy-day uniform now.
```
Trace:
```
[1] parse_query
      in:  looking for a y2k top size S
      out: {'description': 'looking for a y2k top', 'size': 'S', 'max_price': None}
[2] search_listings (via MCP)
      in:  {'description': 'looking for a y2k top', 'size': 'S', 'max_price': None}
      out: 6 items: Mesh Long-Sleeve Top — Black, Y2K Baby Tee — Butterfly Print, Crochet Halter Top — Cream … +3 more
[3] select
      out: Mesh Long-Sleeve Top — Black ($15.0, depop)
      →    first result goes into session['selected_item']
[4] suggest_outfit
      in:  Mesh Long-Sleeve Top — Black + wardrobe of 10 items
      out: Layer the mesh top over the white ribbed tank top, pair them with the baggy straight-leg jeans, and finish wit…
[5] create_fit_card
      in:  Mesh Long-Sleeve Top — Black + outfit text
      out: found this black mesh long-sleeve top on depop for just $15 and honestly it’s already doing way too much heavy…
```

**Try 3: PASS** — `oversized flannel under $40` — fit card returned

```
Oversized Flannel Shirt — Plaid Red/Black ($22.0, thredUp)
Still not over finding this absolute unit of a red and black flannel on thredUp for just $22. Honestly obsessed with throwing it unbuttoned over a ribbed tank or layering a cropped hoodie underneath depending on the vibe. 90s grunge mode: officially activated.
```
Trace:
```
[1] parse_query
      in:  oversized flannel under $40
      out: {'description': 'oversized flannel', 'size': None, 'max_price': 40.0}
[2] search_listings (via MCP)
      in:  {'description': 'oversized flannel', 'size': None, 'max_price': 40.0}
      out: 5 items: Oversized Flannel Shirt — Plaid Red/Black, Oversized Crewneck Sweatshirt — Vintage Navy, Oversized College Crewneck — Faded Red … +2 more
[3] select
      out: Oversized Flannel Shirt — Plaid Red/Black ($22.0, thredUp)
      →    first result goes into session['selected_item']
[4] suggest_outfit
      in:  Oversized Flannel Shirt — Plaid Red/Black + wardrobe of 10 items
      out: Wear the oversized flannel shirt unbuttoned over the white ribbed tank top, paired with the baggy straight-leg…
[5] create_fit_card
      in:  Oversized Flannel Shirt — Plaid Red/Black + outfit text
      out: Still not over finding this absolute unit of a red and black flannel on thredUp for just $22. Honestly obsesse…
```

**Try 4: PASS** — `chunky sneakers size US 9` — fit card returned

```
Low-Top Canvas Sneakers — Off-White ($20.0, poshmark)
scored these off-white canvas sneakers on poshmark for just $20 and my brain is already running through outfits. honestly debating between wearing them with baggy straight-leg jeans and a grey crewneck today, or switching it up with wide-leg khaki trousers and a vintage black denim jacket tomorrow.
```
Trace:
```
[1] parse_query
      in:  chunky sneakers size US 9
      out: {'description': 'chunky sneakers', 'size': 'US 9', 'max_price': None}
[2] search_listings (via MCP)
      in:  {'description': 'chunky sneakers', 'size': 'US 9', 'max_price': None}
      out: 2 items: Low-Top Canvas Sneakers — Off-White, Knit Cardigan — Chunky Brown
[3] select
      out: Low-Top Canvas Sneakers — Off-White ($20.0, poshmark)
      →    first result goes into session['selected_item']
[4] suggest_outfit
      in:  Low-Top Canvas Sneakers — Off-White + wardrobe of 10 items
      out: Outfit 1: Pair the off-white canvas sneakers with the baggy straight-leg jeans, dark wash and the white ribbed…
[5] create_fit_card
      in:  Low-Top Canvas Sneakers — Off-White + outfit text
      out: scored these off-white canvas sneakers on poshmark for just $20 and my brain is already running through outfit…
```

**Try 5: PASS** — `something cute for a summer picnic` — fit card returned

```
Crochet Halter Top — Cream ($22.0, depop)
Still can’t believe I scored this cream crochet halter top for only $22 on depop! Gonna layer it over a white ribbed tank with wide-leg khaki trousers and chunky boots for that 90s indie sleaze look.
```
Trace:
```
[1] parse_query
      in:  something cute for a summer picnic
      out: {'description': 'something cute for a summer picnic', 'size': None, 'max_price': None}
[2] search_listings (via MCP)
      in:  {'description': 'something cute for a summer picnic', 'size': None, 'max_price': None}
      out: 4 items: Crochet Halter Top — Cream, High-Waisted Denim Shorts — Cutoff, Wide-Leg Linen Trousers — Natural … +1 more
[3] select
      out: Crochet Halter Top — Cream ($22.0, depop)
      →    first result goes into session['selected_item']
[4] suggest_outfit
      in:  Crochet Halter Top — Cream + wardrobe of 10 items
      out: Pair the cream crochet halter top with the baggy straight-leg jeans, vintage black denim jacket, and chunky wh…
[5] create_fit_card
      in:  Crochet Halter Top — Cream + outfit text
      out: Still can’t believe I scored this cream crochet halter top for only $22 on depop! Gonna layer it over a white …
```

**Empty search** (from `python app.py ask 'neon green tuxedo size XXS under $3' --trace`). It is shorter because it stops after step 3:

```
[1] parse_query
      in:  neon green tuxedo size XXS under $3
      out: {'description': 'neon green tuxedo', 'size': 'XXS', 'max_price': 3.0}
[2] search_listings (via MCP)
      in:  {'description': 'neon green tuxedo', 'size': 'XXS', 'max_price': 3.0}
      out: [] (empty)
[3] branch
      →    search returned [] — stopping before suggest_outfit

  Nothing matched 'neon green tuxedo'. Try to raise the price limit above $3, drop or change the size (XXS), or use simpler keywords such as 'tee', 'jeans' or 'jacket'.
```

**The three failure modes, triggered on purpose**

1. Empty search: the message above. It names three things to change.
2. Empty wardrobe (`python app.py ask 'oversized flannel shirt under $40' --empty-wardrobe`): `suggest_outfit` got "wardrobe of 0 items" and returned general advice ("Pair the oversized red and black flannel with vintage light-wash high-waisted denim jeans and a tucked-in black ribbed tank top..."), then the fit card was written normally. No crash and no empty string.
3. Model unavailable: I set a wrong key through the environment (`GEMINI_API_KEY=badkey123 python app.py ask 'cropped cardigan under $60' --trace`) so `.env` was never touched. Search worked, step 4 stopped, and the user saw:

```
[4] model unavailable
      →    The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at ai…

  The outfit helper couldn't reach the AI model, so no outfit or fit card was made. Your search itself worked. Check your API key in .env and your internet connection, then run the same query again. Details: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```

The handlers are in `agent.py::run_agent` (`except ModelUnavailable` and `except MCPError`). Before that handler existed the loop would have let the exception escape as a stack trace.

**On the MCP move:** I moved `search_listings`. In `mcp_server.py` I registered it with a description that names units and types and states the empty case, and in `agent.py::run_agent` I replaced the direct call with `mcp_client.call_tool("search_listings", {...})`. Nothing behaved differently: I compared direct and MCP results for three queries (7 results, 1 result, and an empty result) and the returned lists were equal, including the empty case coming back as `[]` rather than `None`. The only visible difference is speed: each call starts a separate server process, and one search took about 720 ms over MCP against under 1 ms direct (one measurement).

---

## The Improvement

**What I changed:** In `tools.py::search_listings`, a listing now has to match at least half of the query's keywords (rounded up) instead of any one of them. One edit, in the line that decides whether a listing is kept.

**Which failure it was meant to fix:** The criterion 2 miss ("white leather wedding dress" matching a leather jacket on one shared word). I picked this change because the diagnosis put both findings in that one threshold.

### Run Log: After

`python score_eval.py --label after` (`results/run_2026-10-21_0852_after.md`). Same scenarios, same scorer.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | FAIL | MET (4/5) |
| 2. Impossible query stops before suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected item is the item that reached the tools | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2-4 sentences, price, platform, distinct opening | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling and size respected | 10 of 10 | PASS | PASS | PASS | PASS | PASS | MET (10/10) |

**Did it help, and how do I know:** It fixed what it targeted and cost something else. Criterion 2 went from 4/5 to 5/5: "white leather wedding dress" now returns `[]` and the loop stops before `suggest_outfit`. The price is criterion 1's Try 5: "something cute for a summer picnic" now returns nothing (only one of its keywords, "cute", appears in the data) and the run stops with "Nothing matched". Criterion 1 went from 5/5 to 4/5, which still meets its target but exactly at the edge. I think that trade is the right one, because the earlier "pass" on that query was a bad match (a halter top for a picnic), but the user-visible cost is that vague, natural-language requests now return nothing.

---

## Stretch: retry without the size filter (declared before building)

Declared after the improvement above and before writing any of it, as the brief asks. The change: when a search comes back empty and the query had a size, `agent.py::run_agent` searches once more without the size, and tells the user which size it dropped. If the retry is also empty, the loop stops exactly as before. I expect criteria 1 to 5 to stay where they are (none of the scenarios fails *because of* its size), so the proof will be one extra diagnostic query (`'vintage jeans size XXL'`) plus a third run log in the same format. I am not retrying with fewer keywords, because that would let "white leather wedding dress" match the leather jacket again and undo the criterion 2 fix.

---

## What's Still Broken

- **Natural-language queries.** "something cute for a summer picnic" now stops with a message, where a person would expect some suggestions. The search is plain keyword matching with no sense of "summer" or "picnic". What I would do: let the model rewrite the user's request into the data's vocabulary (tee, shorts, linen) before searching, or retry once with half the keywords. I stopped because the brief limits this unit to the MCP move and one improvement.
- **Criterion 4 target is too loose.** It was met at 5/5 against a target allowing one miss, and the card checks (price, platform, sentence count) are all things the prompt hands the model directly. I would tighten it to 5 of 5 and add a check for a detail specific to the item.
- **The loop is slow over MCP.** Each search starts a fresh server process. Holding the connection open would fix it. I stopped because it makes the failure behaviour harder to reason about.
- **Partial-match tail.** Searches that pass the half-keyword rule can still return weak items at the end of the list (a sweatshirt for "graphic tee"). Nothing in my criteria checks the tail, so I left it.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
