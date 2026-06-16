# Rule: Keep the roadmap and backlog current

The roadmap and backlog are the project's source of structural truth. They must
never drift from reality. This is a hard rule, not a suggestion.

## The two layers

- **`roadmap.json`** → the phases (P0…Pn) and their status. The *why*.
  Rendered to `assets/roadmap.svg` + `site/data.json` by `scripts/update_site.py`,
  and surfaced in `ROADMAP.md` and the live site. **Never hand-edit the SVG or
  `site/data.json`** — they are generated; edit `roadmap.json` and regenerate.
- **`BACKLOG.md`** → the concrete, checkable tasks under each phase. The *what-next*.

## When you finish a unit of work, in the SAME change

1. **Tick the backlog** — flip the item to `[x]` (or add it if it was missing).
2. **Update `roadmap.json`** — bump the phase/item status if the unit moved it
   (`planned` → `in_progress` → `done`). Mark aspirational tails honestly.
3. **Add a `## Changelog` entry** in `README.md` — a new `### vX.Y.Z — date`
   block with bullets. The deploy gate (`scripts/check_changelog.py --require-new`)
   **fails the push** without a new entry, so this is enforced, not optional.
4. **Regenerate** — run `python3 scripts/update_site.py`; commit the regenerated
   `assets/roadmap.svg` + `site/data.json` (a staleness check fails CI otherwise).

## Adding scope

- A genuinely new direction is a **new phase** in `roadmap.json` (e.g. P7 Plugin),
  with its tasks itemized in `BACKLOG.md`.
- A task within an existing phase goes in that phase's `roadmap.json` `items` and
  as a `[ ]` line in `BACKLOG.md`.

## Honesty

Mark what is **aspirational** (needs a backend, a community, etc.) as such — do not
show it as done. The changelog records what *shipped*; the backlog records what is
*planned*; never blur them.
