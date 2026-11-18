---
status: planning
status_changed: 2026-10-15
type: plan
next: Owner reads the implementation notes, decides what `journal/` does in the public repo (B2), then the first push goes to a private repo.
---

# Build a public Copier template repo for the Claude Code + journal project layer

## Summary

This plan builds one public git repo, `npt`, that Copier turns into a
working project layer in one command: a thin `CLAUDE.md`, imported convention files under
`.claude/`, a separate `.claude/bqrs.md` for the plan format, a `journal/` directory, and a
starter `README.md`.

The base template ships no hook and no executable file.

The owner uses SpecKit as the plan development tool. So `CLAUDE.md` and the imported
`conventions.md` carry no plan-format text. They link to `.claude/bqrs.md`, which is not imported.

The template is a **layer**, not a project scaffold. It does not create `pyproject.toml` or
`package.json`. You run `uv init` (or `npm create`) first, then `copier copy`. This is what makes
the same template work for Python, JS/TS, and an existing legacy project.

This plan supersedes my earlier suggestion (in chat, 2026-10-15) to ship Perry's `scripts/`
check files inside the template. The template ships no check scripts.

## Motivation

This is a template to help quickly provide a structure and productivity to new projects. It will use a public template that runs code on the consumer's machine is a supply-chain target. Security is a design input here, not a closing section.

## Scope

In scope: the repo layout, `copier.yml`, the generalised text of every shipped file (below), the
update path, the legacy-adoption mode, the security model, and the tests.

Not in scope: scaffolding a language toolchain; CI for generated projects.

## Options considered

Copier, Cookiecutter, Cookiecutter + Cruft, a plain skeleton + script, a GitHub template repo,
and a Claude skill were compared in chat on 2026-10-15. Copier wins on three points that matter
here: `copier update` (the structure changes often), verbatim copy of unsuffixed files (the
markdown contains `{{ }}` and `{% %}` examples), and `_skip_if_exists` (project-owned files are
never overwritten on update).

One more fact favours Copier on security: a template with **no `_tasks`, no `_migrations`, and no
Jinja extensions** does not need `--trust`. Cookiecutter has no such split.

## Design

### Repo layout

```
npt/
├── copier.yml
├── README.md              # how to use it, and the threat model in five lines
├── SECURITY.md            # how to report a problem
├── LICENSE
├── CHANGELOG.md           # one line per tag; a MAJOR entry says what update will break
├── .github/workflows/test.yml
├── tests/
│   ├── test_generate.py
│   └── fixtures/legacy_project/
└── template/              # copier.yml sets _subdirectory: template
    ├── {{ _copier_conf.answers_file }}.jinja
    ├── CLAUDE.md.jinja
    ├── README.md.jinja
    ├── .gitignore.jinja
    ├── .claude/
    │   ├── conventions.md             # static, no Jinja
    │   ├── bqrs.md                    # static, no Jinja; linked, not imported
    │   ├── architecture_map.md.jinja
    │   └── docs/
    │       ├── environment.md
    │       └── known_gaps.md
    └── journal/
        ├── CHANGELOG.md
        └── misc/.gitkeep          # free-form notes, never scanned
```

A file renders as Jinja only if its name ends in `.jinja`. Every other file is copied byte for
byte. This is why `conventions.md` can show `{{ }}` examples safely.

### Who owns which file

| File | Owner | On `copier update` |
|---|---|---|
| `.claude/conventions.md` | template | Updated. Shown as a diff. |
| `.claude/bqrs.md` | template | Updated. Shown as a diff. |
| `CLAUDE.md`, `README.md` | project | Never touched (`_skip_if_exists`). |
| `.claude/architecture_map.md` | project | Never touched. |
| `.claude/docs/*`, `journal/CHANGELOG.md`, `.gitignore` | project | Never touched. |

The split is the main defence against update conflicts. A project edits `CLAUDE.md` heavily, so
`CLAUDE.md` holds almost nothing the template needs to change later. The rules live in the imported
`conventions.md`, which the project rarely edits.

### `copier.yml`

```yaml
_min_copier_version: "9.19.1"   # the version the tests ran against
_subdirectory: template
_answers_file: .copier-answers.yml
_templates_suffix: .jinja

_skip_if_exists:
  - CLAUDE.md
  - README.md
  - .gitignore
  - .claude/architecture_map.md
  - .claude/docs/environment.md
  - .claude/docs/known_gaps.md
  - journal/CHANGELOG.md

_message_after_copy: |
  Next steps (nothing was run for you):
    git init                                   # if this is a new directory
    Set up the environment                     # see .claude/docs/environment.md
    Fill out README.md and CLAUDE.md
    specify init --here --force --integration claude

project_name:
  type: str
  help: Human-readable project name
  validator: "{% if not (project_name | regex_search('^[^\\n{}%]{1,80}$')) %}1-80 characters, no braces, no percent sign{% endif %}"

one_line_description:
  type: str
  help: One sentence for CLAUDE.md and README.md
  validator: "{% if not (one_line_description | regex_search('^[^\\n{}%]{1,200}$')) %}1-200 characters, one line, no braces{% endif %}"

language:
  type: str
  help: Primary language (drives .gitignore and the Commands block only)
  choices: [python, typescript, python+typescript, other]
  default: python

source_dir:
  type: str
  help: Directory whose files the architecture map tracks
  default: src
  validator: "{% if not (source_dir | regex_search('^[A-Za-z0-9_./-]+$')) %}letters, digits, _ . / - only{% endif %}"

```

The adoption question (`adopting_existing`) is not in v0.1. An answer nothing reads is a defect,
and adoption mode ships in v0.2 (B3). `_skip_if_exists` already keeps an existing `README.md` and
`CLAUDE.md`.

No question asks for a secret or an email address. Copier writes every answer to
`.copier-answers.yml`, and that file is committed to the generated project.

### The generalised text blocks

These are the portable parts of Perry's `CLAUDE.md` and `docs/conventions.md`. Everything
Perry-specific is removed: the pipeline-stage naming rule, the "policy" disambiguation, the run
story genre, the infrastructure and data-store references, and the dated history. Do not copy Perry's files
into the template wholesale (see B2).

The plan-review rule and the BQRS plan shape are split out of `conventions.md` into their own
file, `bqrs.md`. `CLAUDE.md` links to it and does not import it.

#### `template/CLAUDE.md.jinja`

````markdown
# CLAUDE.md — {{ project_name }} orientation

This file is for whoever (human or Claude) picks this project up next. **It is deliberately
thin.** It holds what is true regardless of task, and what Claude must apply on every task.
Everything else lives one link away, and is read when the task touches it.

**Before adding a dated `## ... (YYYY-MM-DD)` section here: don't.** Write a one-line entry in `journal/CHANGELOG.md` instead. See "Maintaining
CLAUDE.md" in `.claude/conventions.md`.

## What this is

{{ one_line_description }}

<!-- Replace with 2-4 sentences: what the project does, for whom, and which spec or design
     document is authoritative. Link it. -->

## How this file is organized

- **`.claude/conventions.md`** (always loaded, imported below) — standing rules: how to cite a
  section, how to maintain this file and the architecture map.
- **`.claude/architecture_map.md`** (always loaded, imported below) — where each capability lives
  in code. Read it before touching code.
- **`.claude/bqrs.md`** (not imported) — the BQRS plan shape and the plan-review rule. Read it
  when you write or review a feature development plan that uses that shape. Skip it when plans come from another tool such as SpecKit.
- **`.claude/docs/environment.md`** — setup, dependency pinning, provider quirks. Read when
  touching the environment, or before running a one-off script outside the normal commands.
- **`.claude/docs/known_gaps.md`** — the living "not yet done" list. Read before building near an
  area that might already have a known gap.
- **`journal/CHANGELOG.md`** — one line per feature or design change, newest first, each linking to its plan or spec or a summary of how it came to be.
- **`journal/misc/`** — free-form notes.

## Commands

{% if language in ['python', 'python+typescript'] -%}
- Run tests (Python): `uv run pytest`
{% endif -%}
{% if language in ['typescript', 'python+typescript'] -%}
- Run tests (TypeScript): `npm test`
{% endif -%}

@.claude/conventions.md
@.claude/architecture_map.md
````

The Jinja `if` blocks are the only logic. A project that wants other commands edits this list;
the file is project-owned after generation.

#### `template/.claude/conventions.md` (static)

````markdown
# Conventions and standing preferences

Rules Claude must apply on any future task of the relevant kind. This file is always loaded
(imported from `CLAUDE.md`), so keep it small: every line costs context on every session.

## How to cite a section (standing preference)

**A section reference always names its document.** Never a bare `S8` or `§8`, in prose, in code
comments, or in chat.

```
S8 in cache_invalidation.md     <- section 8 of that document
B4 in cache_invalidation.md     <- blockers and questions keep their own IDs
```

If naming the document feels redundant because you just named it, name it anyway. The redundancy
costs a few words, and the ambiguity costs a reader. In conversation, never use a section symbol
for something said in chat rather than written in a file. Say "as I noted earlier", or quote it.

## Maintaining `.claude/architecture_map.md` (standing preference)

The map is only worth reading if it is updated in the same change that moves the ground truth.

**When a task creates or deletes a file under `{source_dir}`, update the map in that same task,
before calling the task done.**

- A **new module** gets a row: its name, what it does in one or two sentences, which plan it
  belongs to, and anything a future reader would otherwise have to rediscover.
- A **deleted module** gets its row struck through with what superseded it, or removed outright if
  nothing did. Say which. A row that silently vanishes reads as an oversight.
- A **rename or move** is a deletion plus a creation. Do both halves.

Editing an existing module without creating or deleting a file does not need a map update. When
unsure, add a row: an extra line costs little, and a missing one costs a search.

## Maintaining `CLAUDE.md` (standing preference)

**Root `CLAUDE.md` and this file never receive a dated, per-change narrative section.** A `##`
heading that ends in a `(YYYY-MM-DD)` date is what a change write-up looks like when it lands in
the wrong file.

- A code-based feature change gets one thing by default: one line in `journal/CHANGELOG.md` that links to it. Nothing else.
- A change earns a line in `CLAUDE.md` or this file only if it states a reusable rule a
  *future, unrelated* task must apply. Test it with the blocker question: would getting this
  wrong later be quietly incorrect, or only a missed chance to know history? Only the first
  belongs here.
- Target size for `CLAUDE.md`: under about 300 lines. If it grows past that, audit before adding.
````

Note the one placeholder in this static file, `{source_dir}`, is single-braced on purpose: a
static file is not rendered. The architecture map (rendered) states the real directory, and this
line tells the reader to look there. If that is too subtle, make `conventions.md` a `.jinja` file
and accept that it needs escaping care. Recommended: keep it static (Q3).

#### `template/.claude/bqrs.md` (static)

The two sections below were in `conventions.md`. They move here under a short header.
`bqrs.md` is template-owned like `conventions.md`, and it is linked from `CLAUDE.md`, not
imported. It costs no context until a task needs it. A project that plans with SpecKit can leave
it unread.

````markdown
# BQRS: the plan shape and the plan review

This file is not imported by `CLAUDE.md`. Read it when you write or review a plan that uses the
BQRS shape. A project that writes plans with another tool does not need it.

## How to review a plan (standing preference)

A review is not finished until the plan carries two things:

1. **Blockers** — anything where a wrong answer produces a system that is quietly *incorrect*,
   not merely suboptimal.
2. **Questions** — what is genuinely undecided, where any answer yields a working system.

**Every blocker and every question gets an explicit recommendation.** Not a survey of options,
not "it depends". A decision should be a *review of a proposal*, not a fresh analysis.

**Ground each recommendation in this project's own history and principles**, not in general
software advice. Start from this seed list. Replace it, and extend it, with the lessons this
project has paid for.

- A value written with no reader, or a state that cannot be reached, is a defect. Grep for a
  reader before believing a field does something.
- A test that agrees with the bug proves nothing. A negative control that does not fail has
  proved nothing.
- Measure before tuning, and set the bar before seeing the data.
- Report first: surface what a real run observes, then write the fix from that evidence.
- Prefer refusing or raising over guessing.
- Removing dead code invalidates prose that cites it. A symbol's dependents include comments,
  docs and journal entries.

**If a review finds no blockers, say so and say why.** An absent section reads as an unfinished
review. The same applies to questions.

## The shape of a plan (BQRS)

A plan's decision part is four sections, in this order: **B**lockers, **Q**uestions,
**R**ecommendations, **S**equencing. They come after the explanatory sections (summary,
motivation, design, scope) and before any dated notes.

- Each blocker carries `[open]` or `[resolved]` on its first line.
- **Recommendations** restates each open blocker's and question's recommendation by ID, without
  re-arguing it.
- **Sequencing** says what must land first, what it must not be bundled with, and what can run in
  parallel.
````

#### `template/.claude/architecture_map.md.jinja`

````markdown
# Architecture map

Where each capability lives in code. Read on nearly every task. Update it in the same task that
creates or deletes a file under `{{ source_dir }}/` (see `.claude/conventions.md`).

| Area | Code | Notes |
|---|---|---|
| _(example)_ Entry point | `{{ source_dir }}/main` | Replace this row. |
````

#### `template/README.md.jinja`

````markdown
# {{ project_name }}

{{ one_line_description }}

## Layout

| Path | What it holds |
|---|---|
| `CLAUDE.md` | Orientation for Claude Code and for humans. Thin on purpose. |
| `.claude/` | Imported conventions, the architecture map, the BQRS plan shape, optional reference docs. |
| `journal/misc/` | Free-form notes. Not checked. |
| `journal/CHANGELOG.md` | One line per change, newest first. |

## Working on this project

Plan before building. Follow `.claude/conventions.md`. The BQRS plan shape is in
`.claude/bqrs.md`.
````

#### `template/.claude/docs/environment.md` and `known_gaps.md` (static starters)

````markdown
# Environment

Setup steps, dependency pinning, provider or API quirks, and the checklist before a first live
run. Keep this file to facts a reader cannot get by reading the code.

- Setup: _(fill in)_
- Secrets: how they reach the process, and which ones do not _(fill in)_
````

````markdown
# Known gaps

The living "not yet done" list. One line per gap: what is missing, why it matters, and the plan
document that tracks it, if any. Remove a line in the same change that closes the gap.
````

#### `template/journal/CHANGELOG.md` (static)

````markdown
# Changelog

One line per change, newest first. Each line links to the plan or spec that carries the full account, or summarises how the change came about.

<!-- YYYY-MM-DD — what changed — [plan or spec](path/to/it.md) -->
````

### Updating projects

```bash
# new project
uv init my-project && cd my-project
uvx copier copy https://github.com/<org>/npt.git . --vcs-ref <tag-or-sha>

# later, pull template changes
uvx copier update --vcs-ref <tag-or-sha>
```

The `uv init` first order above is superseded: see "Corrections (2026-11-18)" at the end, and
0002_new_project_script.md.

`copier update` does a three-way merge between the version in `.copier-answers.yml`, the new
version, and the project's current files. It needs a clean git working tree. Only template-owned
files change, so conflicts should be rare.

### Adopting an existing project (`adopting_existing: true`)

This mode exists because the owner said legacy use will come later. It is not built in v0.1.

- Copier is run against the existing directory. `_skip_if_exists` keeps `README.md` and
  `CLAUDE.md` as they are.
- A generated `ADOPT.md` lists the two `@` import lines to paste into the existing `CLAUDE.md`.

## Security model

The template is public and runs inside the consumer's project. 

| Threat | Answer |
|---|---|
| A compromised template repo runs code on the consumer's machine at `copier copy`. | The template has **no `_tasks`, `_migrations`, or Jinja extensions**, so it needs no `--trust`. A test fails if one is added (T4, T7). |
| A moved tag delivers different content than was reviewed. | Pin by commit SHA, not by tag. Record the SHA in the consumer's notes. Sign release tags with `git tag -s`. Check whether GitHub's immutable-release setting is available and turn it on. |
| An answer is rendered into a file in a way that changes its meaning. | Every answer that reaches a file has a `validator:` regex: no braces, no percent sign, no newline. The template ships no script and no JSON. |
| Secrets or personal data enter the public repo. | No question asks for them. `.gitignore` covers `.env` and `.claude/settings.local.json` (only if the template `.gitignore` is written; see Corrections, 2026-11-18). CI runs a secret scanner and a grep gate (T5). GitHub secret scanning and push protection are on. |
| The consumer's `.copier-answers.yml` leaks something. | It holds only the answers above, none of which is secret. Never add a `secret: true` question without re-reading this table. |
| Account takeover of the maintainer. | Passkey or hardware 2FA. Branch protection on `main`. Tag protection ruleset. No force-push. CI actions pinned by SHA, `permissions: contents: read`. |

## Verification

Each test below runs in `tests/test_generate.py` against a generated temp directory.

| ID | Test | Negative control |
|---|---|---|
| T1 | Generate with defaults. `CLAUDE.md`, `README.md`, `.claude/conventions.md`, `.claude/bqrs.md`, `.claude/architecture_map.md`, `.claude/docs/*`, `journal/CHANGELOG.md` and `.copier-answers.yml` exist. `.claude/hooks/` and `.claude/settings.json` do not. | Add a `.claude/settings.json` to a scratch copy of the template. The test must fail. |
| T2 | Generate at tag A. Edit `CLAUDE.md`. Tag B changes `conventions.md`. `copier update` changes `conventions.md` and leaves `CLAUDE.md` byte-identical. | Change a `_skip_if_exists` file in tag B. Update must still leave the project's copy alone. |
| T3 | Adoption fixture with its own `README.md` and `CLAUDE.md`: neither is overwritten, `ADOPT.md` appears. | — |
| T4 | `copier copy` without `--trust` succeeds. | T7. |
| T5 | Scrub gate: no `/home/`, no `@gmail`, no `perry`, no `terrastep`, no AWS access-key IDs, no PEM private-key headers, no bucket names in `template/`. | Plant a `/home/x` string. The gate must fail. |
| T6 | No `{{` or `{%` in any generated file. | Plant one in a `.jinja` file. The test must fail. |
| T7 | Add a `_tasks` entry in a scratch copy. `copier copy` without `--trust` must refuse. | This is the negative control for T4. |
| T8 | Generate with defaults. `CLAUDE.md` links `.claude/bqrs.md` and has no `@` import of it. `conventions.md` does not contain the word "Blockers". | Add `@.claude/bqrs.md` to a scratch `CLAUDE.md`. The test must fail. |
| T9 | Every `@path`, and every backticked path in "How this file is organized", in the generated `CLAUDE.md` names a file or directory that exists in the generated tree. | Delete `.claude/bqrs.md` from a scratch template. The test must fail. |
| T10 | Generate with defaults and record a checksum of every file. Run `specify init --here --force` with the key from Q8. Every template file is byte-identical afterwards. Runs in a CI job with a pinned `specify` CLI. Resolves B4. | SpecKit's own files (a `.specify/` directory, as far as I know) must appear. If they do not, init did not run and the comparison proves nothing. |

## Blockers

### B1 — The `--trust` boundary [resolved]

Resolved 2026-10-15: `copier.yml` has no `_tasks`, `_migrations` or `_jinja_extensions`. T4 and T7
pass.

If any `_tasks` entry ships, every consumer must pass `--trust`. Then a compromise of this repo is
code execution on every consumer's machine, and the consumer cannot tell which update added it.

**Recommendation.** Zero `_tasks`, zero `_migrations`, zero Jinja extensions in v0.x. Print the
next steps with `_message_after_copy` and let the consumer run them. T4 and T7 enforce this. If a
future version needs a task, that is a MAJOR bump and needs its own plan.

### B2 — Perry-private content must not enter a public repo [open]

Perry's files contain private operational detail: infrastructure layout, credential-handling
history, data-store names, and the owner's home paths. A wholesale copy into a public repo cannot
be un-published: the content may be cached and indexed even if deleted.

**Recommendation.** Write every template file from the generalised blocks in this plan, never
from a copy of a Perry file. Run T5 on every commit. Make the first push to a private repo, run
the gate, read the full tree once by hand, then make it public.

### B3 — Adoption must never overwrite project-owned files [open]

On a legacy project, a template that overwrites `CLAUDE.md` or `README.md` does damage that looks
like success: the project's own content is replaced by generic text, with no error.

**Recommendation.** `_skip_if_exists` on all project-owned files. A generated `ADOPT.md` lists the
`@` import lines and links to paste into the existing `CLAUDE.md`. Ship adoption mode in v0.2,
after one greenfield project has used v0.1. T3 is its test. B4 may reuse this mode.

### B4 — `specify init --here --force` may overwrite template files [resolved]

Resolved 2026-10-15 against `specify` 1.1.1: it changed no template file. It added
`.specify/` and `.claude/skills/speckit-*/`, wrote no `CLAUDE.md`, and removed nothing. T10 holds
the line and runs in CI with the CLI pinned to 1.1.1. It passed on a GitHub runner on
2026-10-15. The original risk text follows.

The next-steps message tells the consumer to run `specify init --here --force`. `--force` skips
the non-empty-directory prompt. SpecKit may write `CLAUDE.md` or files under `.claude/`. I have
not checked which paths it writes. If it overwrites `CLAUDE.md` or `.claude/conventions.md`, the
consumer loses the template's text with no diff, and no test in T1 to T9 notices. T2 covers only
`copier update`.

**Recommendation.** Before build, run the command in a scratch generated project and diff the
tree. T10 is that diff, automated. If it overwrites any template file, choose one of: drop
`--force`; or run SpecKit first and apply the template in adoption mode (B3). Decide from the
diff, not before.

## Questions

### Q1 — License

**Recommendation.** MIT. A template should be reusable without friction.

### Q2 — Where optional docs live

**Recommendation.** `.claude/docs/`, as you asked for the `.claude` directory to hold the
optional markdown too. The `CLAUDE.md` "How this file is organized" list is what makes them
discoverable, so every optional file must have a line there.

### Q3 — Should `conventions.md` be static or rendered

**Recommendation.** Static. It is the file projects update most. A rendered file needs escaping
for every `{{` it shows, and the single `{source_dir}` placeholder costs less than that.

### Q4 — Where the repo lives

**Decision (owner, 2026-10-15).** The repo lives under the personal account, on purpose. This
replaces the earlier recommendation of an organisation account. The cost is that the account name
and the commit author email are visible in a public repo's history.

### Q5 — Versioning

**Recommendation.** SemVer tags `vX.Y.Z`. MAJOR when an update could remove a file or break an `@`
import in a project. MINOR for a new optional file. PATCH for text fixes. Every tag gets one
`CHANGELOG.md` line.

### Q6 — Ship SpecKit's files through Copier

**Recommendation.** No. `specify init` writes SpecKit's own files. A second copy shipped by Copier
would be two sources that go stale on different schedules. The next-steps message runs the
command. B4 covers what that command may overwrite.

### Q7 — Migrate Perry onto the template

**Recommendation.** Not in this plan. Perry's `CLAUDE.md` holds project-specific rules the
template must not absorb. Take Perry's *generic* edits back from the template when they
stabilise, not before.

### Q8 — What the next-steps message passes to `--integration`

The message prints `specify init --here --force --integration <key>` with a literal placeholder.

**Recommendation.** Print the Claude Code key, because this template is a Claude Code layer. The
key is `claude`; verified against `specify init --help` (1.1.1) on 2026-10-15. Do not make it a
Copier question until a second integration is needed.


## Recommendations

In priority order. Reasoning is under each ID above.

1. **B4** — Before build, run `specify init --here --force` in a scratch generated project and
   diff the tree. T10 automates that diff. Decide the next-steps wording from the result.
2. **B1** — No `_tasks`, `_migrations` or Jinja extensions in v0.x. Tests T4 and T7 hold the line.
3. **B2** — Write files from this plan's blocks. First push private. Scrub gate T5 on every commit.
4. **B3** — Skip-if-exists on all project-owned files. Ship adoption mode in v0.2.
5. **Q6, Q8** — SpecKit's files come from `specify init`, not Copier. Name the Claude Code
   integration key, and check it against `specify init --help`.
6. **Q1, Q2, Q3, Q4, Q5, Q7** — MIT; `.claude/docs/`; static `conventions.md`; the personal
   account (owner decision, 2026-10-15); SemVer tags; Perry out of scope.

## Sequencing

1. **First, and before any code:** resolve B1 and B2 by owner approval. They shape every file.
   Run the B4 scratch check by hand at the same time. Its result may change the next-steps text.
2. **Then:** build the repo privately: `copier.yml`, the files above, and T1 to T9. Add T10
   once B4 is settled. Do not bundle the adoption mode (B3) into the first commit; add it as its
   own tagged change so a problem is traceable to one.
3. **Then:** one greenfield project uses v0.1, runs `specify init`, and runs `copier update` once
   against a v0.1.1. That is the first real test of the update path and of the SpecKit step. Make
   the repo public only after this.
4. **After v0.1 is public:** build adoption mode (v0.2) and test it on one throwaway copy of an
   older project, never on Perry first.
5. **Must not be bundled with:** the Perry migration (Q7). It is a different decision with a
   different failure mode.

## Implementation notes (2026-10-15)

v0.1 is built in this directory. Nothing is committed or pushed.

- **Built:** `copier.yml`, the `template/` tree from the blocks above, `README.md`, `SECURITY.md`,
  `LICENSE`, `CHANGELOG.md`, `.github/workflows/test.yml`, `tests/`.
- **Tests:** `uv run --with copier==9.19.1 --with pytest pytest -q tests` gives 22 passed. T1 to
  T10 each have their negative control, except T3, which has none.
- **Left out of v0.1 on purpose:** the `adopting_existing` answer and `ADOPT.md` (B3, v0.2). T3
  covers the part that exists: an existing `README.md` and `CLAUDE.md` are kept.
- **Changed from the blocks above:**
  - The `CLAUDE.md` "How this file is organized" line for `conventions.md` no longer lists
    "plan status", since that section is gone.
  - The Commands block prints `Run tests: _(fill in)_` for `language: other`, so the heading is
    not empty.
  - The Commands lines are labelled `(Python)` and `(TypeScript)`, so `python+typescript` does not
    print two identical `Run tests:` lines.
  - T5 also bans object-storage URLs.
- **Open for B2:** the first push to a private repo, the full-tree read by hand, and the choice of
  what happens to `journal/`. T5 scans `template/` only, so it does not cover this plan.
- **`LICENSE`** names "npt contributors". Put the real holder in before release.
- **CI** actions are pinned by SHA (`actions/checkout` v4.2.2, `astral-sh/setup-uv` v6.8.0).
  First GitHub run (run 38846519911, commit `a964712`), read with `gh run view --log`: both jobs
  succeeded. The `generate` job shows `21 passed, 1 skipped`, and its secret scan step passed.
  The `speckit` job shows `1 passed, 21 deselected`, so T10 ran on the runner and was not
  skipped. The `generate` job does not pass `-rs`, so its log does not name the skipped test. It
  is T10, the only test with a skip condition.

## Corrections (2026-11-18)

Found while planning 0002_new_project_script.md. Reproduced with Copier 9.19.1 and uv 0.12.23.

- **The `.gitignore` claim holds only in one order.** The security table says the generated
  `.gitignore` covers `.env` and `.claude/settings.local.json`. This plan, and the first
  `README.md`, told the consumer to run `uv init` first, then `copier copy`. `uv init` writes its
  own `.gitignore` (Python entries only). `.gitignore` is in `_skip_if_exists`, so Copier leaves
  it, and the template `.gitignore` is never written. In that flow the result has no `.env` line
  and no `.claude/settings.local.json` line. T1 did not catch it, because T1 generates into an
  empty directory.
- **The same order leaves an empty `README.md` empty.** `uv init` writes a `README.md` with 0
  bytes. `README.md` is in `_skip_if_exists`, so it stays empty.
- **Fix.** Run `copier copy` first, then `uv init`. `uv init` does not overwrite existing files.
  The bootstrap script `scripts/new-project.sh` (installed as `npt-copier`) does this, deletes an
  empty README before Copier runs, and appends missing secret lines to an existing `.gitignore`.
  The repo `README.md` is rewritten to match. Tests N1 and N2 in 0002_new_project_script.md cover
  both cases.
- **The "template ships no script" statement still holds for `template/`.** The bootstrap script
  is outside `template/`, so Copier never copies or runs it, and `--trust` is still not needed.
  It is code the consumer runs, so it has its own blocker (B3 in 0002_new_project_script.md).
- **Test count.** After 0002 is built the suite has 53 tests: T1 to T10 from this plan, and N1 to
  N11 from 0002.
- **Pushed.** Everything in this plan is on `main` (`a964712`, `33615e3`). The "nothing is
  committed or pushed" line in the 2026-10-15 notes is out of date. 0002 landed as `75f4499`.
- **Recommendations entry for Q4 corrected (2026-11-18).** The entry said "an organisation
  account". The Q4 item records the owner's decision: the personal account. The entry now says so.
  Found by the check in 0003_bqrs_one_solution_two_places.md. The grouped one-line entries in
  Recommendations are shorter than their items but not wrong, so they are left as written.
