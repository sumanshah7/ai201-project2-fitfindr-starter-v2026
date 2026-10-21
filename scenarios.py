"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

def _s(name, query, criterion, wardrobe="example"):
    return {"name": name, "query": query, "wardrobe": wardrobe, "criterion": criterion}


# score_eval.py runs these. For criteria 1-4 each scenario is ONE try, so five
# scenarios under a criterion = its five tries (five different queries, as
# criteria.md words them). Criterion 5 is about search output only, so its ten
# queries are checked through the MCP search tool without calling the model.
SCENARIOS = [
    # 1. Matching queries (varied phrasing on purpose — criterion 1's reason is
    #    that some phrasings will miss).
    _s("c1 graphic tee", "vintage graphic tee under $30", 1),
    _s("c1 y2k top", "looking for a y2k top size S", 1),
    _s("c1 flannel", "oversized flannel under $40", 1),
    _s("c1 sneakers", "chunky sneakers size US 9", 1),
    _s("c1 vague phrasing", "something cute for a summer picnic", 1),
    # 2. Impossible queries — must stop before suggest_outfit.
    _s("c2 ballgown", "designer ballgown size XXS under $5", 2),
    _s("c2 tuxedo", "neon green tuxedo size XXS under $3", 2),
    _s("c2 wedding dress", "white leather wedding dress", 2),
    _s("c2 cheap parka", "winter parka under $2", 2),
    _s("c2 tiara", "diamond tiara size M", 2),
    # 3. State — any queries that match.
    _s("c3 jeans", "vintage jeans size W30", 3),
    _s("c3 track jacket", "90s track jacket", 3),
    _s("c3 cardigan", "knit cardigan under $60", 3),
    _s("c3 band tee", "band tee size L", 3),
    _s("c3 cargo", "cargo pants under $40", 3),
    # 4. Fit card — five different items.
    _s("c4 graphic tee", "graphic tee under $30", 4),
    _s("c4 corduroy", "corduroy pants", 4),
    _s("c4 denim jacket", "denim jacket under $50", 4),
    _s("c4 hoodie", "vintage hoodie", 4),
    _s("c4 boots", "combat boots", 4),
    # Diagnostic: an empty wardrobe (not one of the five).
    _s("empty wardrobe", "denim jacket under $50", None, wardrobe="empty"),
]

# 5. Price ceiling and size respected — checked on search output alone.
# (description, size, max_price)
CRITERION_5_QUERIES = [
    ("graphic tee", None, 30.0), ("jeans", "W30", None), ("jacket", None, 40.0),
    ("top", "M", None), ("vintage", "S", 25.0), ("pants", "W28", 35.0),
    ("shoes", "US 9", None), ("sweatshirt", "L", 30.0), ("tee", None, 15.0),
    ("dress", "M", 50.0),
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
