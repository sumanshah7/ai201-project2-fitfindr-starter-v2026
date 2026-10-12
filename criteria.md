# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
I picked 4 of 5 because my search is a plain keyword match over 40 listings, so a
phrasing like "something cute for summer" shares no words with any listing and
will miss, and the two model calls can also fail (rate limit, empty reply). 5 of 5
would punish me for vocabulary the data doesn't have, not for a broken agent.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
5 of 5 because this path calls no model at all: it is a regex parse, a list
filter and an `if not results` check, all deterministic. If it fails once, that is
a bug in the branch, not variation.

---

## 3. Something about state

On 5 queries that match at least one listing, in 5 of 5 tries
`session["selected_item"]["id"]` equals `session["search_results"][0]["id"]`, and
the `id` of the item passed into `suggest_outfit` and into `create_fit_card` (checked
by wrapping each function to record its argument) is that same id.

**Why this target:**
5 of 5, with no allowance for misses. Nothing random happens between the search
and the hand-off, so a single mismatch means the loop passed the wrong value or
overwrote it, and that should never be tolerated. I compare ids, not titles,
because two listings can share a title.

---

## 4. Something about the fit card

Across fit cards for 5 different items (one try each), at least 4 of 5 cards
meet all of: 2 to 4 sentences; contains the item's price as "$N"; contains the
item's platform name; and none of the 5 cards starts with the same first five
words as another.

**Why this target:**
4 of 5 because the model is non-deterministic and may drop the price or write
five sentences once in a while, so I allow one slip. I did not set 3 of 5 because
the price and platform are given to the model in the prompt, so omitting them
more than once in five is a prompt problem I should catch. The first-five-words
rule is there to catch a template-style caption that ignores the item.

---

## 5. Your choice

The price ceiling and size are always respected: over 10 different queries that
include a ceiling and/or a size, 10 of 10 returned listings have
`price <= max_price` and a size that matches the requested size as a whole token
(so "M" never returns "XL" or "US 9").

**Why this target:**
10 of 10 because it is a plain filter, and a thrift shopper who says "under $30"
and gets a $45 jacket will stop trusting the search. I chose it because the
starter warns that substring size matching quietly returns the wrong items, and
this is the check that would catch it.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
