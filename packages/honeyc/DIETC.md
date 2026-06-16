# DietC — modular nutrition compiler on HoneyC

> **Not medical advice.** DietC is a software tool for modeling intake as
> coverage vectors. All bundled nutrient numbers are **examples for testing**,
> not authoritative nutrition data. It does not diagnose or treat anything.

DietC treats every ingestible thing — food, drink, pill, powder, bar, oil,
sauce, supplement — as a **module** that contributes to (and sometimes risks)
a set of coverage vectors. It computes what a day is missing (gaps), what it
overshoots (caps), and which modules would patch the gaps without breaching a
cap.

```txt
Food groups are a public-health interface.
Coverage vectors are the deeper machine.
```

Vitamins alone are insufficient because a food group encodes far more than a few
micronutrients — fiber/fermentable substrate, the food matrix, phytochemicals,
satiety, displacement of worse foods, long-term risk pattern. DietC models those
as explicit vectors (`NutrientVector`, `MatrixVector`, `SafetyVector`) so a day
can be *technically patched yet still flagged as a poor pattern*.

## Pipeline

```txt
Intake → Vectors → DayState → Gaps/Caps → PatchPlan → Warnings → Render
```

```txt
load.py     YAML items / profile / modules / day      →  models
engine.py   events × items → DayState (totals)
gapcap.py   DayState ⇔ GoalProfile → gaps, caps, matrix_gaps, warnings
patch.py    greedy planner: cover gaps, avoid caps, respect preferences
safety.py   conservative warnings (fiber ramp, sodium, sugar-alcohol, dup supplements)
render.py   prose summary           rune.py   Dense Rune-Chain (+ HoneyC passthrough)
```

## Run

```bash
python3 -m pip install --no-build-isolation -e .   # installs honeyc + dietc

dietc compile examples/dietc/potato_day.yaml --profile examples/dietc/default_profile.yaml --modules examples/dietc/patch_modules.yaml
dietc summary examples/dietc/potato_day.yaml --profile examples/dietc/default_profile.yaml
dietc rune    examples/dietc/potato_day.yaml --profile examples/dietc/default_profile.yaml --modules examples/dietc/patch_modules.yaml --honeyc
dietc check   examples/dietc/potato_day.yaml --profile examples/dietc/default_profile.yaml
```

## Data files (all configurable — no nutrition truth is hard-coded)

- `items.yaml` — `{id, name, category, serving_size, nutrient_vector, matrix_vector, safety_vector, tags}`
- `default_profile.yaml` — `{targets, upper_limits, minimum_matrix, preferences, constraints}`
- `patch_modules.yaml` — `{id, contributes, matrix, avoids, dose_min/max/step, warnings, ...}`
- `<day>.yaml` — `{label, items_file, events:[{item_id, amount, unit}]}`

## Example output

`dietc rune` on the potato day:

```txt
[PotatoDay]
  ⇢ CurrentVector
  ⇒ ΔGap:{Calories,Protein,Fiber,Omega3,Potassium,Calcium,Magnesium,MatrixDiversity,MatrixColor,Berry,Greens,Polyphenol}
  ⇒ Patch:{GreenThing,ProteinFiberBar,ElectrolyteWater,Omega3Capsule,BerryThing}
  ⇒ |ImprovedPattern|
```

The patch planner explains every choice (`dietc check`): the Protein Fiber Bar
because protein and fiber are below target (with a "increase fiber gradually"
warning), Electrolyte Water because potassium is needed and it adds no sodium,
the matrix foods because plant/color/polyphenol coverage is low.

## How DietC relates to HoneyC

DietC is a **domain compiler on top of HoneyC**. HoneyC compiles Dense
Rune-Chain notation into IR + lenses; DietC adds a nutrition ontology, a vector
engine, a gap/cap engine, a patch planner, and a safety checker, and emits its
results *as* Dense Rune-Chain — which `dietc rune --honeyc` feeds back through
HoneyC's parser/renderer. DietC is the worked proof that arbitrary domain
compilers (next: attention-chains, CoRs, skillchains) can ride on HoneyC.

## Limitations

- Deterministic MVP; greedy patch planner, not an optimizer.
- No external food databases, barcode, or recipe parsing yet.
- Matrix vectors are additive (not saturating) in the MVP.
- Example data only — supply your own items/profiles/modules for real use.

## Tests

```bash
pytest tests/dietc      # 16 tests: load, totals, gaps/caps, patch, render, honeyc passthrough
```
