# Masters Tournament Results

A static web app showing every Masters Tournament winner from 1934 to the present, with scores, scores to par, and a biography for each champion.

**Live site:** https://212121-ts.github.io/masters-tournament-app/

There is no server, no database, and no build step. The page loads one JSON file and does everything else in the browser. To update the app, you edit that JSON file and commit it.

---

## Files

| File | Purpose |
|---|---|
| `index.html` | The entire app — markup, styles, and logic in one file |
| `masters_data.json` | All tournament results and golfer biographies. **This is the only file you normally edit.** |
| `README.md` | This document |

Nothing else is needed. If you see `main.py`, `requirements.txt`, or `render.yaml` in the repo, they are leftovers from the old Render.com deployment and can be deleted.

## How it works

On page load, `index.html` fetches `masters_data.json` and computes everything from it: the results list, the search index and autocomplete, the four summary statistics, and the biography modal. Statistics like "unique winners" and "most wins" are derived at runtime, so they update themselves — you never edit a count by hand.

Hosting is GitHub Pages, publishing from the `main` branch, root folder. Any commit to `main` republishes the site within about a minute.

---

## Updating the data

The Masters is played once a year, so this happens once a year. Two ways to do it:

**By hand.** Open `masters_data.json` on github.com, click the pencil icon, make the edit, commit. The GitHub editor flags JSON syntax errors in the left gutter — if you see a red marker, do not commit.

**With an AI agent.** Give the agent the prompt below along with the current `masters_data.json`, and have it return the complete updated file. Then paste that into GitHub and commit.

### Prompt for the agent

Copy everything inside the block, fill in the facts at the top, and attach the current `masters_data.json`.

````text
You are editing the data file for a static Masters Tournament web app. The attached
masters_data.json is the single source of truth for the entire site. Your job is to add
one new tournament result and make sure the corresponding golfer entry is correct.

FACTS FOR THIS UPDATE
  Year:              [e.g. 2027]
  Winner:            [full name as commonly written, e.g. Scottie Scheffler]
  72-hole score:     [total strokes, e.g. 277]
  Score to par:      [negative number under par, e.g. -11; use 0 for even]
  Nationality:       [3-letter code, e.g. USA]

(If any of these are blank and you have web access, look them up from a reliable source
— the official Masters site, the PGA Tour, or a major sports outlet — and state which
source you used. If you cannot verify a value, stop and say so rather than guessing.)

FILE STRUCTURE

The file is a single JSON object with exactly two top-level keys, "tournaments" and
"golfers". Do not add, rename, or remove any keys anywhere in the file.

A tournament object — one per year played:

    {
      "year": 2026,
      "winner": "Rory McIlroy",
      "score": 276,
      "to_par": -12,
      "nationality": "NIR"
    }

A golfer object — one per champion, never more than one per person:

    {
      "name": "Rory McIlroy",
      "bio": "Rory McIlroy completed one of golf's greatest achievements by...",
      "total_majors": 6,
      "turned_pro": 2007,
      "nationality": "NIR"
    }

WHAT TO DO

1. Insert the new tournament object at the TOP of the "tournaments" array. That array is
   ordered newest year first and must stay that way.

2. Check whether the winner already appears in "golfers", matching on "name".

   If they are already there (a repeat champion): do NOT add a second entry. Update the
   existing one instead — rewrite the "bio" to incorporate the new victory, and increase
   "total_majors" by one. Leave "turned_pro" and "nationality" alone unless they are wrong.

   If they are a first-time champion: add a new golfer object, positioned alphabetically
   by SURNAME among the existing entries (the array runs Aaron ... Zoeller). Set
   "total_majors" to their career major championship total including this win, and
   "turned_pro" to the year they turned professional.

3. Write the bio in the same voice as the existing ones: third person, factual, roughly
   40 to 90 words, present tense for who they are and past tense for what they did.
   Mention the Masters win, the year, and one or two specifics that make it memorable —
   the margin, a decisive shot, a record, a first. Name their other majors with years if
   they have them. No hype, no exclamation marks, no emoji, no second person.

4. Spell the winner's name IDENTICALLY in the tournament object and the golfer object.
   The app matches biographies to results on that exact string, so a mismatch silently
   produces a champion with no bio. Keep accents and punctuation as they appear in the
   name (e.g. "José María Olazábal", "Mark O'Meara", "Ángel Cabrera").

RULES

- Change nothing else. Do not reformat, re-sort, or "tidy" any part of the file you were
  not asked to touch. Do not correct existing bios unless the new result makes one wrong.
- Match the existing formatting exactly: 2-space indentation, double-quoted keys and
  string values, no trailing commas.
- "score" and "to_par" are numbers, not strings. "to_par" is negative for under par.
- "nationality" is a 3-letter uppercase code. Codes already in use: ARG, AUS, CAN, ENG,
  ESP, FJI, GER, JPN, NIR, RSA, SCO, USA, WAL. Note that ENG, SCO, WAL, and NIR are used
  rather than GBR.
- There is no entry for 1943, 1944, or 1945 — the tournament was not played during the
  war. Do not fill those years in.

BEFORE YOU RETURN ANYTHING

Validate that the file parses as JSON. A single missing comma has broken this file
before, and the site will show nothing but an error if it happens again. If you can run
code, actually parse it and confirm. Then verify all of the following:

  - The file parses cleanly.
  - "tournaments" gained exactly one entry and is still ordered newest first.
  - "golfers" gained exactly one entry, or gained none and had one updated.
  - Every distinct "winner" in "tournaments" has a matching "name" in "golfers".
  - No duplicate years in "tournaments" and no duplicate names in "golfers".

OUTPUT

Return the COMPLETE updated masters_data.json as a single file — not a diff, not a
snippet, not just the changed section. Follow it with a short plain-language summary:
what you added, whether the golfer entry was new or updated, the source you used for the
result, and confirmation that the file parses and the checks above passed.
````

After the agent returns the file, paste it into `masters_data.json` on github.com and commit. The site updates itself within a minute or so — no redeploy, no restart.

---

## Data reference

`masters_data.json` contains two arrays.

**`tournaments`** — one object per year the tournament was played, ordered newest first. Currently 90 entries covering 1934 through 2026; 1943 to 1945 are absent because the tournament was suspended during the Second World War.

| Field | Type | Notes |
|---|---|---|
| `year` | number | Four digits, unique across the array |
| `winner` | string | Must exactly match a `name` in `golfers` |
| `score` | number | 72-hole total strokes |
| `to_par` | number | Negative under par, `0` for even |
| `nationality` | string | 3-letter uppercase code |

**`golfers`** — one object per champion, ordered alphabetically by surname. Currently 57 entries.

| Field | Type | Notes |
|---|---|---|
| `name` | string | Must exactly match the `winner` string used in `tournaments` |
| `bio` | string | Roughly 40–90 words, third person |
| `total_majors` | number | Career majors, all four championships |
| `turned_pro` | number | Year |
| `nationality` | string | 3-letter uppercase code |

Masters win counts are **not** stored — the app counts them from `tournaments` at runtime. Adding a repeat champion's second win to `tournaments` updates their "Masters Wins" figure automatically.

---

## Working on it locally

Opening `index.html` by double-clicking it will show an empty page. Browsers block `fetch()` from `file://` URLs, so the app cannot read the JSON that way. To preview locally, serve the folder over HTTP instead. From a terminal, in the folder containing the two files:

    python3 -m http.server 8000

Then open `http://localhost:8000` in a browser. Press Ctrl+C in the terminal to stop it.

## Troubleshooting

**The page loads but shows "Tournament data could not be loaded."** The JSON is malformed. Paste the file into a JSON validator, or open the browser console (F12) — the error message names the problem.

**A champion's name opens a modal that says "Bio information not available."** The `winner` string in `tournaments` does not exactly match any `name` in `golfers`. Check for a spelling difference, a missing accent, or a stray space.

**An edit is committed but the site looks unchanged.** Give it a minute, then hard-refresh (Ctrl+Shift+R, or Cmd+Shift+R on a Mac). If it still looks stale, check the Actions tab on GitHub — a failed Pages build shows up there.
