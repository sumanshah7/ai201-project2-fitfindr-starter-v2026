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
- **Returns:** A list of at most `config.SEARCH_RESULT_LIMIT` (10) listing dicts, best match first. Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`. Size is a whole-word match (`M` matches `S/M` and `M/L`, never `XL` or `US 9`; `One Size` matches anything).
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

The happy path (`python app.py ask 'vintage graphic tee under $30'`) calls the model and
has NOT been run yet: `.env` still holds the placeholder `GEMINI_API_KEY`.
TODO: paste its real output here once the key is added.

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; r=search_listings('graphic tee', max_price=30); print([(x['id'],x['title'],x['price']) for x in r])"
[('lst_006', 'Graphic Tee — 2003 Tour Bootleg Style', 24.0), ('lst_002', 'Y2K Baby Tee — Butterfly Print', 18.0), ('lst_033', 'Vintage Band Tee — Faded Grey', 19.0), ('lst_015', 'Vintage Graphic Hoodie — Faded Black', 26.0), ('lst_017', 'Mesh Long-Sleeve Top — Black', 15.0), ('lst_012', 'Oversized Crewneck Sweatshirt — Vintage Navy', 20.0), ('lst_011', 'Low-Rise Cargo Pants — Khaki', 27.0)]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
TODO: not run yet (needs the API key).
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
TODO: not run yet (needs the API key).
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

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



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
