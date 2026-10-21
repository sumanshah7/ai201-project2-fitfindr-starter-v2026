"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable
from mcp_client import call_tool, MCPError


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    session["parsed"] = parse_query(query)
    parsed = session["parsed"]
    trace.step("parse_query", inputs=query, returned=str(parsed))

    try:
        iterations = 0
        step = "search"
        while step != "done":
            iterations += 1
            trace.check_iterations(iterations)

            if step == "search":
                args = {
                    "description": parsed["description"],
                    "size": parsed["size"],
                    "max_price": parsed["max_price"],
                }
                session["search_results"] = call_tool("search_listings", args)
                trace.step("search_listings (via MCP)", inputs=str(args),
                           returned=session["search_results"])
                # THE BRANCH: nothing found -> explain and stop, never call the model tools.
                if not session["search_results"]:
                    session["error"] = _no_results_message(parsed)
                    trace.step("branch", note="search returned [] — stopping before suggest_outfit")
                    return session
                session["selected_item"] = session["search_results"][0]
                trace.step("select", returned=session["selected_item"],
                           note="first result goes into session['selected_item']")
                step = "outfit"

            elif step == "outfit":
                session["outfit_suggestion"] = suggest_outfit(
                    session["selected_item"], session["wardrobe"]
                )
                trace.step("suggest_outfit",
                           inputs=f"{session['selected_item']['title']} + wardrobe of "
                                  f"{len(session['wardrobe'].get('items') or [])} items",
                           returned=session["outfit_suggestion"])
                step = "card"

            elif step == "card":
                session["fit_card"] = create_fit_card(
                    session["outfit_suggestion"], session["selected_item"]
                )
                trace.step("create_fit_card",
                           inputs=f"{session['selected_item']['title']} + outfit text",
                           returned=session["fit_card"])
                step = "done"

    except ModelUnavailable as exc:
        session["error"] = (
            "The outfit helper couldn't reach the AI model, so no outfit or fit card "
            f"was made. Your search itself worked. Check your API key in .env and your "
            f"internet connection, then run the same query again. Details: {exc}"
        )
        trace.step("model unavailable", note=str(exc)[:100])
    except MCPError as exc:
        session["error"] = (
            "The listing search service didn't respond, so nothing was searched. "
            "Run `python mcp_server.py` on its own to see the error, then try again. "
            f"Details: {str(exc).splitlines()[0]}"
        )
        trace.step("mcp error", note=str(exc).splitlines()[0])

    return session


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE = re.compile(
    r"(?:under|below|less than|max|up to|<=?)\s*\$?\s*(\d+(?:\.\d+)?)|\$\s*(\d+(?:\.\d+)?)",
    re.I,
)
_SIZE = re.compile(
    r"\bsize\s+((?:us\s*)?[a-z]*\d*(?:\s*l\d+)?(?:/[a-z]+)?)\b",
    re.I,
)


def parse_query(query: str) -> dict:
    """Regex parse: pulls a price ceiling and a size out, the rest is the description."""
    max_price = None
    m = _PRICE.search(query)
    if m:
        max_price = float(m.group(1) or m.group(2))
    size = None
    m = _SIZE.search(query)
    if m and m.group(1).strip():
        size = m.group(1).strip()
    description = _PRICE.sub(" ", query)
    description = _SIZE.sub(" ", description)
    description = re.sub(r"\s+", " ", description).strip(" ,.")
    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    tips = []
    if parsed["max_price"] is not None:
        tips.append(f"raise the price limit above ${parsed['max_price']:.0f}")
    if parsed["size"]:
        tips.append(f"drop or change the size ({parsed['size']})")
    tips.append("use simpler keywords such as 'tee', 'jeans' or 'jacket'")
    return (
        f"Nothing matched '{parsed['description']}'. Try to " + ", ".join(tips[:-1])
        + (", or " if len(tips) > 1 else "") + tips[-1] + "."
    )


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
