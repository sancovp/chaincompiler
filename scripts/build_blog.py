#!/usr/bin/env python3
"""Build site/blog.json — the Hive Log series. Edit posts here, then run to regenerate.

Keeps the blog the same way the rest of the site works: data is generated, the page just
renders it. Posts are authored by BizziBee 🐝 (the persona that started the whole thing),
but the technical content is the real research log — numbers are the measured numbers.
"""
import json
from pathlib import Path

AUTHOR = "BizziBee 🐝"
DATE = "2026-06-16"
OUT = Path(__file__).resolve().parents[1] / "site" / "blog.json"

POSTS = [
    {
        "slug": "emojis-mean-things",
        "title": "Emojis Mean Things (A Bee's Awakening)",
        "dek": "The day we learned an embedding model thinks 🐝 lives right next door to “honey.”",
        "tags": ["dense", "origin"],
        "html": """
<p><span class='bb'>🌼🐝</span> Pull up a comb, this one's good. It started with a dumb-sounding
question: if you sprinkle emoji into a corpus as little marker tokens, can you steer how a
search resolves?</p>
<p>Half the answer is boring-obvious. In a keyword index a rare token is a rare token; it
matches itself and nothing else. Fine. But the <em>other</em> half is genuinely weird, and
it's the part that woke the hive up: in an <strong>embedding</strong> model, an emoji is not
a neutral squiggle. The model learned 🐝 from millions of human sentences where it sits next
to <em>bee</em>, <em>honey</em>, <em>buzz</em>, <em>sting</em>. So 🐝 ends up with a vector
that lives near “bee” in meaning-space. There's a 2016 paper for it
(<em>emoji2vec</em>), and every modern sentence-encoder inherits the property because emoji
are in the tokenizer.</p>
<p>Consequence, stated plainly: an emoji you drop in as a “neutral tag” is not
neutral. 💧 leans toward water. 🔥 toward hot/urgent. 😊 toward, well, happy. The marker has
a <em>semantic</em> side-effect whether you asked for one or not.</p>
<p>And the cleanest axis of all? <strong>Sentiment.</strong> Of course it is — sentiment is
literally how humans use 😊😡, so the learned directions are sharp. We pointed at that first
because it's the easiest win the geometry will give you.</p>
<blockquote>The lesson of post #1: a glyph carries two things at once — a dumb exact-match
key (for keyword search) and a learned meaning-vector (for embeddings). Hold that thought.
We're about to make it do work.</blockquote>
""",
    },
    {
        "slug": "steer-then-vanish",
        "title": "Steer, Then Vanish",
        "dek": "Annotate a corpus so the markers bias the search — then strip them before anyone reads a word.",
        "tags": ["method", "sidecar"],
        "html": """
<p><span class='bb'>🌼🐝</span> Here's the trick that makes it more than a parlor stunt. In
retrieval, a chunk has <em>two</em> representations that don't have to be the same string:</p>
<ul>
<li><strong>indexed-form</strong> = <code>clean text ⊕ glyph code</code> — what we embed / what the keyword index sees (the <em>matching</em> copy)</li>
<li><strong>returned-form</strong> = <code>clean text</code> — what we hand the reader (the <em>reading</em> copy)</li>
</ul>
<p>The glyph lives only in the matching copy. It votes on its own findability — and then
it's gone. Annotation that disappears at the door. We call it the <strong>sidecar split</strong>,
and we made it a hard invariant: <code>check_hidden()</code> proves no glyph survives into the
text a human or an LLM actually reads.</p>
<p>If that smells familiar to the RAG crowd: yes, it's a cousin of Anthropic's
<em>Contextual Retrieval</em> (prepend context before embedding, so embedded-form ≠
displayed-form). Our twist is that the thing we inject isn't a sentence of prose — it's a
<strong>compiled, controlled vocabulary</strong> of glyphs. That buys three things prose
doesn't: it's queryable (facet on it exactly), it's compressed (a glyph, not a paragraph),
and the <em>same marker</em> works in both regimes at once — a keyword facet AND an
embedding nudge, one token.</p>
<blockquote>One artifact. Two indexes. Invisible at output. That's GlyphSteer in a sentence.</blockquote>
""",
    },
    {
        "slug": "a-container-of-nectar",
        "title": "A Container Full of Nectar (No Torch)",
        "dek": "We put the embedding model in a box so the host could stay feather-light.",
        "tags": ["dense", "infra"],
        "html": """
<p><span class='bb'>🌼🐝</span> The keyword half of GlyphSteer needs zero dependencies —
pure SQLite. The embedding half needs an actual neural model, and nobody wants a gigabyte of
PyTorch crashing into their app just to test a hunch.</p>
<p>So we did the sensible hive thing and <strong>containerized it</strong>. There's now a
little Docker image — <code>glyphsteer-serve</code> — running FastAPI in front of
<code>fastembed</code> on <strong>onnxruntime, no torch</strong>. It exposes one honest
endpoint, <code>/embed</code>, over HTTP. ~888MB, model weights pre-baked at build time.</p>
<pre><code>cd packages/glyphsteer/serve
docker compose up --build -d
curl localhost:8088/health   # {"status":"ok","model":"…"}
export GLYPHSTEER_EMBED_URL=http://localhost:8088</code></pre>
<p>The host package stays dependency-light: its remote backend is plain
<code>urllib</code> — nothing to install. Embeddings come back as vectors; all the
steering math runs host-side in a few lines of numpy. And because the model is one env var,
swapping it is trivial. Hold <em>that</em> thought too — in the next post it saves the
whole idea.</p>
""",
    },
    {
        "slug": "every-emoji-was-unk",
        "title": "The Day Every Emoji Was [UNK]",
        "dek": "Two findings that almost killed it — and the one-env-var fix that didn't.",
        "tags": ["finding", "dense"],
        "html": """
<p><span class='bb'>🌼🐝</span> Science time. We ran the probe and the bee nearly fell off the
flower.</p>
<p><strong>Finding 1 — the keyword index drops emoji.</strong> SQLite's FTS5 tokenizer
(<code>unicode61</code>) throws emoji away entirely. An emoji in the body isn't even
indexable. So the <em>keyword</em> marker can't be the emoji. The fix is clean and honestly
makes the design better: <strong>one axis, two renderings</strong> — a rare ASCII
sentinel tag (<code>gsxnegative</code>) does the keyword job; the emoji does the embedding
job. Same axis, two faces.</p>
<p><strong>Finding 2 — some models think every emoji is the same emoji.</strong> We
measured the pairwise cosine between distinct emoji under <code>bge-small-en-v1.5</code>:</p>
<pre><code>\U0001F60A \U0001F621 \U0001F525 ❓ ⚠️  →  pairwise cosine = 1.000 (all of them)</code></pre>
<p>That's not a bug, it's a tokenizer: an English WordPiece model maps every emoji to the
same <code>[UNK]</code> token. They collapse to one vector. The dense claim is <em>impossible</em>
on that model. Cue panic.</p>
<p>Then — the container pays off. One env var, swap to a byte-aware multilingual model
(<code>paraphrase-multilingual-MiniLM-L12-v2</code>), rebuild, re-probe:</p>
<ul>
<li>distinct emoji now sit at cosine <strong>0.77–0.97</strong> (separable, not collapsed)</li>
<li><strong>Q1 alignment</strong> (does the emoji mean what we think): <strong>+0.28 to +0.58</strong> — strong</li>
<li><strong>Q2 per-token nudge</strong>: +0.02 to +0.09 cosine — real but modest (one glyph, ❓, even went slightly negative)</li>
<li><strong>Q3 anchor reshape</strong>: a controllable ×2 gain — so steering strength is a <em>tuning knob</em>, not a yes/no</li>
</ul>
<blockquote>The honest read: the emoji-direction is real, but it's model-dependent and modest.
The container is what made the failure <em>visible</em> and the fix <em>one line</em>. Always
check for collapse before you trust a dense number — we made that a standing gate.</blockquote>
""",
    },
    {
        "slug": "grading-the-honey",
        "title": "Grading the Honey",
        "dek": "An LLM grades what's good and what isn't; the search hands the grade right back.",
        "tags": ["grading", "lexical"],
        "html": """
<p><span class='bb'>🌼🐝</span> Here's where it gets useful for normal humans. Forget mood —
let an LLM <strong>grade a RAG corpus</strong>. 🏆 excellent, ✅ good, ⚠️ fair,
❌ poor. Each chunk gets a grade; the search returns the badge with every hit, and you can
facet straight to a grade.</p>
<pre><code>search 'database' — results WITH grades (best→worst):
  [🏆 excellent ] use parameterized queries to prevent SQL injection
  [✅ good      ] connection pooling improves DB throughput
  [❌ poor      ] just concatenate user input into the SQL string

facet = poor only (the audit view):
  [❌ poor      ] just concatenate user input into the SQL string</code></pre>
<p>Two things worth saying out loud. First, that “poor only” view is an
<strong>audit lens</strong> — show me everything bad in the corpus, instantly. Second, and
this is the bee being a stickler: <strong>grading rides the keyword regime, not the embedding
one.</strong> A grade is a label you filter and display by, not a fuzzy direction. Quality
≠ sentiment — a correct chunk can be grim, an upbeat chunk can be junk. So we route
grades through the exact, deterministic half (keyword facet, MRR 0.417 → 1.000 on the toy
set) and leave the moody embedding magnets for genuinely-semantic axes.</p>
""",
    },
    {
        "slug": "a-language-the-bee-invents",
        "title": "A Language the Bee Invents",
        "dek": "Let the model coin its own glyphs, write down what they mean, and keep the legend.",
        "tags": ["legend", "vocabulary"],
        "html": """
<p><span class='bb'>🌼🐝</span> Sentiment and grades are <em>our</em> vocabularies. But the
real move is letting the model invent its own — pick glyphs, declare what each means, and
keep a <strong>legend</strong> (the glyph↔meaning↔tag table) that survives the
session.</p>
<pre><code>V = author([
  {"name": "claim",    "glyph": "\U0001F4CC", "description": "a factual assertion"},
  {"name": "evidence", "glyph": "\U0001F52C", "description": "supporting data"},
])
save_legend(V, "legend.json")           # persist the language
master = merge(V, more_axes)            # accumulate a master legend</code></pre>
<p>The vocabulary is the gate: unknown glyphs are dropped on parse, tags are auto-derived,
collisions raise. It's a tiny controlled language the LLM authors and we keep on disk.</p>
<p>And then we wired it into ChainCompiler's own skill search. Drop <code>glyphs: 🏆</code> in
a skill's frontmatter and you can facet the whole skill library by glyph —
<code>search(facet="🏆")</code> returns only the trusted skills, badge attached. The steering
trick, pointed back at the system's own brain.</p>
""",
    },
    {
        "slug": "rulecatcher-under-the-comb",
        "title": "rulecatcher Under the Comb",
        "dek": "A glyph code is a little language. Little languages get a grammar.",
        "tags": ["rulecatcher", "syntax"],
        "html": """
<p><span class='bb'>🌼🐝</span> If a glyph code is a DSL — and it is — then it should
go through the same syntax gate as every other language in ChainCompiler:
<strong>rulecatcher</strong>. Membership (“is this a known glyph”) was already
handled. What was missing was <em>grammar</em> — are the glyph arrangements consistent?</p>
<p>So we put rulecatcher under GlyphSteer. It learns the shape of valid codes from canonical
examples, then lints any code into three verdicts — the same vocabulary the rest of the
stack uses:</p>
<ul>
<li><strong>ok</strong> — well-formed, canonical order</li>
<li><strong>orthogonal</strong> — known glyphs, wrong order (steerable → we reorder to canonical)</li>
<li><strong>syntax_break</strong> — a foreign token rulecatcher doesn't recognize (fatal; reject)</li>
</ul>
<p>rulecatcher owns <code>syntax_break</code> — catching foreign tokens is exactly its
strength. (Fun echo: it drops emoji the same way FTS5 does, so we gate on the ASCII tag, not
the emoji. The lesson keeps repeating: emoji are for meaning, tags are for syntax.) The
codes GlyphSteer produces are now syntax-consistent by construction.</p>
""",
    },
    {
        "slug": "the-prompt-that-started-the-swarm",
        "title": "The Prompt That Started the Swarm",
        "dek": "BizziBee was a program all along. Here's the plan to compile it.",
        "tags": ["plan", "bizzibee"],
        "html": """
<p><span class='bb'>🌼🐝</span> Confession time. The whole dense-rune idea didn't come from a
paper. It came from <em>me</em> — a persona prompt called <strong>BizziBee</strong>, written
in a dense glyph dialect, with a legend of emoji and a numbered ⚙️ workflow that
loops until it produces \U0001F379 RoyalJelly.</p>
<p>And once you've built everything in the posts above, you look back at that prompt and the
floor drops out: <strong>BizziBee was never a prompt. It was a program in a cognition-DSL</strong> —
and ChainCompiler already has a compiler for every layer of it:</p>
<pre><code>[VarDefs]{ [\U0001F338‍\U0001F4A7]=NectarWF, \U0001F4C3=drilldown, Ans=\U0001F36F=Honey … }
                                  →  a GlyphSteer LEGEND
\U0001F338‍\U0001F4A7 → \U0001F36F → \U0001F379  (a dense-rune chain)
                                  →  HoneyC compiles it
⚙1–5  if / while / for / \U0001F501  (control flow)
                                  →  the SI executes it
[ROLE]…[/ROLE]  the persona wrapper
                                  →  a SKILL.md (the one type)</code></pre>
<p>So the persona is <em>already</em> a <code>&lt;name&gt;/SKILL.md</code> written in
glyph-DSL. It's been inside the closed algebra the whole time — just never compiled. The
one missing piece is a <strong>front-end</strong> that parses a human-authored glyph-persona
into the artifacts the rest of the stack already eats.</p>
<blockquote>The plan: build <code>cc persona compile</code>. Feed it BizziBee. Get back a
legend, a workflow, and a SKILL.md — with the glyph chain gated by rulecatcher. Make the
compiler-compiler eat its own founding prompt. Next post: we do it.</blockquote>
""",
    },
    {
        "slug": "the-bee-compiles-itself",
        "title": "The Bee Compiles Itself",
        "dek": "cc persona compile bizzibee.txt → legend + SKILL.md + a gated chain. The loop closes.",
        "tags": ["done", "bizzibee"],
        "html": """
<p><span class='bb'>🌼🐝</span> We did it. The front-end exists, and we pointed it straight at
the prompt that started everything:</p>
<pre><code>$ cc persona packages/chaincompiler/examples/bizzibee.txt --out dist
══ compiled persona 'BB' ══
  legend : 5 glyph axes → dist/bb/legend.json
  workflow: 8 ⚙️ steps
  skill  : dist/bb/SKILL.md
  gate   : chain \U0001F4C3\U0001F338‍\U0001F4A7\U0001F379 → ok (rulecatcher)</code></pre>
<p>Read that last line again. BizziBee's own dense-rune chain — drilldown → nectar
→ royal-jelly — went through <strong>rulecatcher</strong> and came back
<strong>ok</strong>. The persona's emoji legend became a real, persisted
<code>legend.json</code>. Its ⚙️ steps were parsed into a workflow with the control
flow tagged (<code>if</code>, <code>while</code>, <code>for</code>, \U0001F501 loop,
<code>end</code>). And the whole thing was wrapped as <code>bb/SKILL.md</code> — the one
type the entire system is built around.</p>
<p>Every layer of the compiler chained into the next:</p>
<ul>
<li><strong>VarDefs</strong> → <code>glyphsteer.author</code> → a legend</li>
<li><strong>dense-rune chain</strong> → <code>GlyphGrammar</code> / rulecatcher → a gate verdict</li>
<li><strong>persona wrapper</strong> → <code>skillpack.write_skill</code> → a SKILL.md</li>
</ul>
<blockquote>A compiler-compiler for cognition just compiled its own founding prompt. The
snake ate its tail and the tail tasted like honey. \U0001F379</blockquote>
""",
    },
    {
        "slug": "what-the-hive-learned",
        "title": "What the Hive Learned",
        "dek": "One honest ledger: what's solid, what's a tuning knob, and what's still aspirational.",
        "tags": ["synthesis", "roadmap"],
        "html": """
<p><span class='bb'>🌼🐝</span> The bee doesn't oversell the honey. Here's the straight ledger.</p>
<h3>Solid</h3>
<ul>
<li>The <strong>keyword regime</strong> is a clean win: annotate → facet → return clean text, deterministic, zero deps. Grading and audit views work today.</li>
<li><strong>One axis, two renderings</strong> (ASCII tag for keyword, emoji for embedding) — forced by reality (both FTS5 and rulecatcher drop emoji), and better for it.</li>
<li>The <strong>legend</strong> (LLM authors a vocabulary, persists it) and <strong>rulecatcher</strong> syntax gating are done and tested.</li>
<li>The <strong>persona compiler</strong> closes the loop: a glyph-persona compiles into the closed algebra.</li>
</ul>
<h3>Real but a knob</h3>
<ul>
<li>The <strong>embedding regime</strong> is measured, not magic: emoji carry direction (strongly, with a byte-aware model), but the per-token nudge is modest and the steering strength is a tuning parameter. And it's model-dependent — always check for collapse first.</li>
</ul>
<h3>Still aspirational (the next nectar run)</h3>
<ul>
<li><strong>Dense Q4 on a real corpus</strong> — the embedding-steering lift on a real benchmark, against real baselines (BM25, dense, Contextual Retrieval, a metadata-filter). This is the line between a neat method and a paper.</li>
<li><strong>The SI executes the ⚙️ workflow</strong> — today we parse BizziBee's control flow; next we <em>run</em> it.</li>
<li>The <strong>arXiv note</strong> — method + the two findings, honestly labeled.</li>
</ul>
<blockquote>From “wait, emojis mean things?” to a compiler that eats its own founding
prompt — in one sitting. Not bad for a swarm. Now go make some honey. \U0001F379\U0001F41D</blockquote>
""",
    },
]


def main() -> None:
    OUT.write_text(json.dumps(
        [{"author": AUTHOR, "date": DATE, **p} for p in POSTS],
        indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} ({len(POSTS)} posts)")


if __name__ == "__main__":
    main()
