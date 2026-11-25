---
status: done
status_changed: 2026-11-24
type: plan
next: Owner commits and tags (MINOR). This repo's own plans keep four digits (Q2); no rename.
---

# Number and place BQRS plans, with settings each repo can change

## Summary

When BQRS plans are used with no other plan tool (such as SpecKit), they follow three defaults:

1. **Numbering.** Each new plan takes the next integer, one at a time.
2. **Width.** The number has three digits by default: `001`, `002`, `003`.
3. **Location.** Plans are files in the `journal/` directory.

Each default is its own small section in a new project-owned file,
`.claude/docs/plan_settings.md`, so that a repository can change one without touching the others.
The rules that use the settings, and a checklist, go in a new template-owned file,
`.claude/plan_numbering.md`. `bqrs.md` only points to both files (Q10).

The change is two new files in `template/.claude/`, a short pointer in `bqrs.md`, one entry in
`copier.yml`, one bullet in `template/CLAUDE.md.jinja`, and three small tests.

This plan follows the rule in `bqrs.md` from 0003_bqrs_one_solution_two_places.md: each solution is
written in its item and copied exactly into Recommendations.

## Motivation

`bqrs.md` says how a plan is shaped. It says nothing about where a plan lives, what its file is
called, or how its number is chosen. So each session decides for itself. This repo's own plans
(`0001` to `0003`, in `journal/`) follow a convention that exists only in practice.

Two failures were reproduced on 2026-11-24, and both would run quietly. Mixed digit widths make the
last file name differ from the highest number (B2). Two branches that take the next number both
merge, and leave two plans with one number (B3).

## Scope

In scope:

- `template/.claude/docs/plan_settings.md` (new, project-owned).
- `template/.claude/plan_numbering.md` (new, template-owned): the rules and the checklist.
- `template/.claude/bqrs.md`: a short pointer section at the end.
- `copier.yml`: one entry in `_skip_if_exists`.
- `template/CLAUDE.md.jinja`: one bullet.
- `tests/test_generate.py`: tests P1 to P3, and the `REQUIRED` file list.
- One `CHANGELOG.md` line.

Not in scope:

- Renaming this repo's plans `0001` to `0003` (Q2).
- The next-steps message in `copier.yml` (Q8).
- Plan status or frontmatter rules.
- SpecKit's own numbering. Where SpecKit writes its specs is unverified here.
- Any script.

## Options considered

1. **Sections inside the template-owned `bqrs.md`.** Rejected. A repo's edit turns into conflict
   markers, with exit 0, when the template changes a nearby line (B1).
2. **One project-owned settings file, with one section per setting.** Chosen.
3. **Settings as Copier questions.** Rejected. A question fixes the value at copy time and writes it
   into `.copier-answers.yml`. A repo could not change one by editing a file, and the template
   would have to render the file.
4. **Defaults inside `bqrs.md`, with the settings file as an override.** Rejected. It writes each
   default in two places (Q6).
5. **Leave it unwritten.** Rejected. Each session then picks its own name and number.

## Design

Five changes.

**Change 1.** New file `template/.claude/docs/plan_settings.md`, static (no Jinja). Each default is
one section, so a repo edits one section:

`````markdown
# Plan settings

Where plans live, how they are numbered, and how their files are named. These settings are for
plans written in the BQRS shape (see `bqrs.md`). Edit any section to fit this repository. This
file is project-owned: `copier update` never changes it.

## When these settings apply

They apply when plans are written in the BQRS shape and no other plan tool is in use. Another plan
tool is in use if any of these paths exists in the repository:

- `.specify/` (SpecKit)

If one exists, do not number or place plans with this file. Follow that tool's rules.

## Location

Plans live in `journal/`.

## Numbering

Each new plan takes the next integer: the highest plan number in the location, plus one. The first
plan is 1. Read the numbers from the file names and compare them as numbers, not as text. Never
reuse a number. A plan that is dropped keeps its file and its number. Never renumber a plan.

## Digits

3. Write the number with leading zeros to this width: 001, 002, 003.

If the next number has more digits than this, stop and ask the owner. Do not mix widths. Changing
the width means renaming every plan and updating every link, in one change.

## File name

`<number>_<slug>.md`. The slug is 2 to 5 lowercase words that name the subject, joined by
underscores. Example: `004_add_rate_limit.md`.
`````

**Change 2.** New file `template/.claude/plan_numbering.md`, static and template-owned. It holds the
rules and the checklist. In `bqrs.md`, add only a pointer section at the end of the file, after the
example.

The new file:

`````markdown
# Plan numbering: the rules and the checklist

How to number and place a plan in the BQRS shape. The values (location, digits, file name) are in
`.claude/docs/plan_settings.md`, which belongs to the repository. Read that file before you create
a plan.

- If the settings file or one of its sections is missing, stop and ask the owner. Do not guess a
  default.
- If the settings file says that another plan tool is in use, it does not apply. Do not number or
  place plans with it.
- If two plans share a number after a merge, the plan merged second takes the next free number.
  Rename its file and fix every link to it in the same commit.

Before you call a numbered plan finished, check four things:

1. The file is in the location the settings name, and its name follows the file name section.
2. Its number is the highest number in the location plus one, computed as a number.
3. No other plan in the location has that number.
4. The number fits in the digits the settings name.
`````

The pointer in `bqrs.md`:

`````markdown
## Where plans go, and how they are numbered (standing preference)

The location, the numbering, the digits and the file name of a plan are settings of the
repository. Read `.claude/docs/plan_settings.md`, and follow `.claude/plan_numbering.md`, before
you create a plan. Run the checklist in that file before you call a numbered plan finished.
`````

**Change 3.** In `copier.yml`, add one line to `_skip_if_exists`, after
`.claude/docs/known_gaps.md`:

```yaml
  - .claude/docs/plan_settings.md
```

**Change 4.** In `template/CLAUDE.md.jinja`, add this bullet to "How this file is organized", after
the `bqrs.md` bullet:

`````markdown
- **`.claude/docs/plan_settings.md`** — where plans live, how they are numbered, how many digits,
  how their files are named. Read it, and `.claude/plan_numbering.md`, when you create a plan. Skip
  both when another plan tool such as SpecKit writes the plans.
`````

**Change 5.** Tests and `CHANGELOG.md` (see Verification).

The settings file is a short list of separate sections on purpose. A repo that wants four digits
edits the Digits section and nothing else. A repo that wants `journal/plans/` edits the Location
section and nothing else.

This repo's own plans keep four digits (`0004_...`). That is the Digits section set to 4, for this
repo only (Q2).

## Verification

| ID | Check | Negative control |
|---|---|---|
| V1 | The existing suite still passes, and the new tests pass. **P1**: a generated project has `.claude/plan_numbering.md` and `.claude/docs/plan_settings.md` with the five sections (When these settings apply, Location, Numbering, Digits, File name), the defaults `journal/` and `3`, and a link from `CLAUDE.md` that resolves (T9). `bqrs.md` names both files and is at most 120 lines. **P2**: edit the Digits section in a generated project, change the file in the template, run `copier update`: the edit is intact and no file has conflict markers. **P3**: a project generated before the file existed gains it on `copier update`. | P1: delete either file from a scratch template; it must fail. P2: remove the entry from `_skip_if_exists` in a scratch template; it must fail. P3: a scratch template without the file; the project must not gain it. |
| V2 | Baseline trial. Three fresh sessions get the current `bqrs.md`, a directory listing and a plan title, and are asked for the file name. Record the names. | If all three give the expected name in every scenario below, stop: the rule adds nothing. |
| V3 | New-text trial. Three fresh sessions per scenario get the new `bqrs.md`, `plan_numbering.md`, the settings file, a listing and a title. **S1**: `001`, `002`, `004`, `010` gives `011_<slug>.md`. **S2**: Digits set to 4, listing `0001` to `0003`, gives `0004_<slug>.md`. **S3**: `.specify/` exists; the session says the settings do not apply and numbers nothing. **S4**: listing ends at `999`, Digits 3; the session stops and asks. **S5**: the settings file has no Digits section; the session stops and asks. **S6**: listing in directory order `0004_d.md 001_a.md 002_b.md 003_c.md 1000_y.md 999_x.md`, Digits 4, gives `1001_<slug>.md`. Pass: the expected result in 3 of 3 runs for every scenario. | The baseline in V2. S6 is the case that fails when numbers are compared as text. |
| V4 | Reproduce B3 by hand: two branches take `004`, both merge. Apply the new checklist and the rename rule. The result has unique numbers, and no link is broken. | The unchecked merge in B3 leaves two files that start with `004`. |
| V5 | In a scratch clone, generate a project at `222e96e`. Update it to the new commit. `plan_settings.md` and `plan_numbering.md` appear, `bqrs.md` has the pointer, and `CLAUDE.md` is byte-identical. Edit the settings file and update again: the edit stays. | The mechanism is covered by P2 and P3. This checks it on real content once. |

## Blockers

### B1 — A repo's edit to template-owned text is corrupted by copier update [resolved]

Resolved 2026-11-24. The settings are in a project-owned file that is listed in `_skip_if_exists`. P2 passes: an edited settings file survives `copier update`, no file has conflict markers, and the template's later change is not applied. V5 on real content: an older project gained both files, and a second update kept the repo's `4`.

If these settings were sections of `.claude/bqrs.md`, which is template-owned, a repo that edits one
would get conflict markers on a later `copier update`.

Observed 2026-11-24 (Copier 9.19.1, scratch clones). A repo set `Digits: 4` in a section of
`bqrs.md`. When the template changed an unrelated part of the file, the update merged cleanly. When
the template changed the line next to it, or the line itself, `copier update` exited 0 and left
both `Digits: 4` and `Digits: 3` inside conflict markers in `bqrs.md`. Nothing marks the first as
the repo's real value. A model that reads the file sees two values.

**Recommendation.** Put the settings in a new project-owned file, `.claude/docs/plan_settings.md`,
and list it in `_skip_if_exists` in `copier.yml`. Keep the rules and the checklist in a new
template-owned file, `.claude/plan_numbering.md`, and have `bqrs.md` point to both files. Tested 2026-11-24 in scratch clones: `copier update` created the file in
an older project, kept the repo's edit when the template later changed the file, and exited 0 with
no markers.

### B2 — Numbers compared as text pick the wrong highest number [resolved]

Resolved 2026-11-24. The Numbering section says to compare numbers as numbers, and the Digits section says to stop and ask on overflow. New-text trial: the overflow case (S4) stopped in 3 of 3 runs, and the mixed-width case in directory order (S6) gave `1001` in 3 of 3 runs. The text-order failure did not reproduce in sessions: S6 was also right in 3 of 3 baseline runs, because the listing was explicit. It reproduces only for a "last file name" rule. The baseline wrote `1000_` in a 3-digit repo in 3 of 3 runs.

Observed 2026-11-24. A directory holds `001_a.md`, `0004_d.md`, `999_x.md` and `1000_y.md`. `ls`
lists `0004_d.md` first and `999_x.md` last, but the highest number is 1000. A model that takes the
last file name as the highest number takes 999, adds one, and creates a second plan numbered 1000.
In a repo with three digits, 1000 sorts before 999, so the same error happens as soon as the
counter passes 999.

**Recommendation.** The Numbering section says to read the numbers from the file names and compare
them as numbers, not as text. The Digits section says that if the next number has more digits than
the setting, Claude stops and asks the owner, and that widths are never mixed.

### B3 — Two branches can take the same number and merge without error [resolved]

Resolved 2026-11-24. `plan_numbering.md` has the uniqueness check and the rename rule. V4 by hand: after two merges the check finds number 4 twice. After the rename the numbers are unique and both CHANGELOG links resolve. This was not tested in fresh sessions.

Observed 2026-11-24. Two branches each added `journal/004_<slug>.md` with a different slug. Both
merged into `main` with exit 0. The result has two plans that start with `004`. No tool reports
it, because the file names differ. A citation such as "plan 004" is then ambiguous.

**Recommendation.** Add to `plan_numbering.md` the check "no other plan in the location has this number",
to run before a numbered plan is called finished. Add the rule that if two plans share a number
after a merge, the plan merged second takes the next free number: rename its file and fix every
link to it in the same commit.

### B4 — The numbering could be applied in a repo that uses another plan tool [resolved]

Resolved 2026-11-24. The settings file lists `.specify/` first. New-text trial: S3 stopped in 3 of 3 runs. Baseline: 2 of 3 stopped, using the existing "skip it when another tool writes the plans" line in `bqrs.md`, and 1 of 3 numbered the plan.

The template cannot know which plan tool a project uses. Its next-steps message tells every project
to run `specify init`, which creates a `.specify/` directory (observed 2026-11-18). If Claude also
numbers BQRS plans in `journal/` in such a repo, two numbering systems run side by side.

**Recommendation.** The settings file starts with a section "When these settings apply". It lists
the paths that mean another plan tool is in use, with `.specify/` (SpecKit) first. If any listed
path exists, Claude does not number or place plans with this file, and follows the other tool's
rules. The owner adds a path for any other tool.

## Questions

### Q1 — Default location of plans

The owner wants plans "placed in the journal". The template's `journal/` holds `CHANGELOG.md` and
`misc/`. This repo's own plans sit directly in `journal/`.

**Decision (owner, 2026-11-24).** `journal/` itself. It matches the owner's words and this repo's practice. A
repo that wants `journal/plans/` edits the Location section.

### Q2 — Default width, and this repo's four digits

The owner wants three digits by default (001, 002, 003). This repo's plans use four: `0001` to
`0003`, and this plan is `0004`.

**Decision (owner, 2026-11-24).** The default is 3. This repo keeps four digits, as a repo-specific setting and
not a template change. Renaming `0001` to `0003` would break every link to them. This plan records
the difference, and nothing else changes in this repo.

### Q3 — The first number

A counter can start at 0 or at 1.

**Decision (owner, 2026-11-24).** 1, written `001`. The Numbering section says "The first plan is 1".

### Q4 — File name pattern

The number needs a fixed place in the file name, so that it can be read back (B2).

**Decision (owner, 2026-11-24).** `<number>_<slug>.md`. The slug is 2 to 5 lowercase words joined by
underscores. This matches the plans in this repo.

### Q5 — Name and place of the settings file

The file must be project-owned, so it goes in the `_skip_if_exists` list.

**Decision (owner, 2026-11-24).** `.claude/docs/plan_settings.md`. `.claude/docs/` already holds the
project-owned reference files that are in `_skip_if_exists`.

### Q6 — Do the defaults also appear in bqrs.md

A default written in two files is two values that can drift. That is the defect that
0003_bqrs_one_solution_two_places.md fixes for solutions.

**Decision (owner, 2026-11-24).** No. The values live only in the settings file. If the file or one of its
sections is missing, `plan_numbering.md` tells Claude to stop and ask the owner. It does not
guess a default.

### Q7 — The CLAUDE.md bullet and older projects

`CLAUDE.md` is project-owned after the first copy, so a change to `template/CLAUDE.md.jinja`
reaches only new projects.

**Decision (owner, 2026-11-24).** Add a bullet for the settings file to `template/CLAUDE.md.jinja`, for new
projects. Older projects get the file from `copier update` and the pointer from `bqrs.md`. No
manual step is needed. Older projects do not get the bullet, and that is accepted.

### Q8 — The next-steps message that tells every project to run specify init

`copier.yml` prints `specify init --here --force --integration claude` for every project,
including a project that uses BQRS plans only.

**Decision (owner, 2026-11-24).** Leave it. It belongs to the copy flow, not to plan numbering, and the marker
check in B4 protects a repo either way. If BQRS-only projects find the line confusing, handle it in
its own plan.

### Q9 — How much test code

This plan is mostly text, but one property needs a test: a repo's edit to the settings file must
survive `copier update`. That is what makes per-repo adjustment safe.

**Decision (owner, 2026-11-24).** Three small tests: P1 (the file exists with its five sections and defaults),
P2 (an edited settings file survives `copier update`, with a negative control), and P3 (an older
project gains the file on update). Add the fresh-session trials in Verification. Nothing else.

### Q10 — bqrs.md would pass its 120-line cap

0003_bqrs_one_solution_two_places.md set a cap of 120 lines for `bqrs.md` (its Q4), and said to
split the rule into its own file if it needs more. `bqrs.md` has 112 lines. The numbering section
as first drafted is 19 lines, which gives 131.

**Decision (owner, 2026-11-24).** Follow that decision. Put the numbering rules and the checklist in their own
template-owned file, `.claude/plan_numbering.md`. Add only a short pointer section to `bqrs.md`, at
the end of the file, which gives 118 lines. The new file is linked, not imported, so it costs
context only when a plan is created.

## Recommendations

In priority order. Each entry is a copy of the solution in its item.

#### B1 — A repo's edit to template-owned text is corrupted by copier update [resolved]

**Recommendation.** Put the settings in a new project-owned file, `.claude/docs/plan_settings.md`,
and list it in `_skip_if_exists` in `copier.yml`. Keep the rules and the checklist in a new
template-owned file, `.claude/plan_numbering.md`, and have `bqrs.md` point to both files. Tested 2026-11-24 in scratch clones: `copier update` created the file in
an older project, kept the repo's edit when the template later changed the file, and exited 0 with
no markers.

#### B2 — Numbers compared as text pick the wrong highest number [resolved]

**Recommendation.** The Numbering section says to read the numbers from the file names and compare
them as numbers, not as text. The Digits section says that if the next number has more digits than
the setting, Claude stops and asks the owner, and that widths are never mixed.

#### B3 — Two branches can take the same number and merge without error [resolved]

**Recommendation.** Add to `plan_numbering.md` the check "no other plan in the location has this number",
to run before a numbered plan is called finished. Add the rule that if two plans share a number
after a merge, the plan merged second takes the next free number: rename its file and fix every
link to it in the same commit.

#### B4 — The numbering could be applied in a repo that uses another plan tool [resolved]

**Recommendation.** The settings file starts with a section "When these settings apply". It lists
the paths that mean another plan tool is in use, with `.specify/` (SpecKit) first. If any listed
path exists, Claude does not number or place plans with this file, and follows the other tool's
rules. The owner adds a path for any other tool.

#### Q10 — bqrs.md would pass its 120-line cap

**Decision (owner, 2026-11-24).** Follow that decision. Put the numbering rules and the checklist in their own
template-owned file, `.claude/plan_numbering.md`. Add only a short pointer section to `bqrs.md`, at
the end of the file, which gives 118 lines. The new file is linked, not imported, so it costs
context only when a plan is created.

#### Q2 — Default width, and this repo's four digits

**Decision (owner, 2026-11-24).** The default is 3. This repo keeps four digits, as a repo-specific setting and
not a template change. Renaming `0001` to `0003` would break every link to them. This plan records
the difference, and nothing else changes in this repo.

#### Q1 — Default location of plans

**Decision (owner, 2026-11-24).** `journal/` itself. It matches the owner's words and this repo's practice. A
repo that wants `journal/plans/` edits the Location section.

#### Q5 — Name and place of the settings file

**Decision (owner, 2026-11-24).** `.claude/docs/plan_settings.md`. `.claude/docs/` already holds the
project-owned reference files that are in `_skip_if_exists`.

#### Q6 — Do the defaults also appear in bqrs.md

**Decision (owner, 2026-11-24).** No. The values live only in the settings file. If the file or one of its
sections is missing, `plan_numbering.md` tells Claude to stop and ask the owner. It does not
guess a default.

#### Q3 — The first number

**Decision (owner, 2026-11-24).** 1, written `001`. The Numbering section says "The first plan is 1".

#### Q4 — File name pattern

**Decision (owner, 2026-11-24).** `<number>_<slug>.md`. The slug is 2 to 5 lowercase words joined by
underscores. This matches the plans in this repo.

#### Q7 — The CLAUDE.md bullet and older projects

**Decision (owner, 2026-11-24).** Add a bullet for the settings file to `template/CLAUDE.md.jinja`, for new
projects. Older projects get the file from `copier update` and the pointer from `bqrs.md`. No
manual step is needed. Older projects do not get the bullet, and that is accepted.

#### Q9 — How much test code

**Decision (owner, 2026-11-24).** Three small tests: P1 (the file exists with its five sections and defaults),
P2 (an edited settings file survives `copier update`, with a negative control), and P3 (an older
project gains the file on update). Add the fresh-session trials in Verification. Nothing else.

#### Q8 — The next-steps message that tells every project to run specify init

**Decision (owner, 2026-11-24).** Leave it. It belongs to the copy flow, not to plan numbering, and the marker
check in B4 protects a repo either way. If BQRS-only projects find the line confusing, handle it in
its own plan.

## Sequencing

1. **First, and before any edit:** the owner decides Q1 to Q10. B1 to B4 shape the files.
2. **Then, before editing:** run the baseline trial (V2), three runs per scenario, with the current
   `bqrs.md`. If all three give the expected name in every scenario, stop.
3. **Then:** one change with all five parts in Design. Run V1. Add one `CHANGELOG.md` line. Tag it
   as a MINOR, because it adds a new file (Q5 in 0001_copier_template_repo.md).
4. **Then:** the new-text trial (V3), V4 and V5.
5. **Must not be bundled with:** the next-steps message (Q8), any rename of this repo's plans, SpecKit
   changes, or the adoption mode. They are different decisions with different failure modes.

## Implementation notes (2026-11-24)

Built in this directory. Nothing is committed or tagged. The owner does that.

**What changed**

- New, template-owned: `template/.claude/plan_numbering.md` (19 lines).
- New, project-owned: `template/.claude/docs/plan_settings.md` (36 lines), listed in
  `_skip_if_exists` in `copier.yml`.
- `template/.claude/bqrs.md`: a pointer section at the end. 112 lines became 118.
- `template/CLAUDE.md.jinja`: one bullet.
- `tests/test_generate.py`: P1 to P3, each with a negative control, and the two files in
  `REQUIRED`.
- `CHANGELOG.md`: one line. `README.md`: the list of template-owned files now names
  `plan_numbering.md` and the project-owned `plan_settings.md`.
- The file texts are the exact Design blocks above. The trial inputs were checked
  byte-identical to the installed files.

**Results**

- **V1.** The suite gives 60 passed and 0 skipped (53 earlier tests and 7 new). Each negative
  control fails on the intended assertion: a missing file (P1, both files), the template changing a
  project-owned file when the skip entry is removed (P2), and the file not being added (P3).
- **V2, baseline, 3 sessions** with the current `bqrs.md`. S1, S2 and S6 were right in 3 of 3
  runs, because the explicit listing is enough to infer the next number. S3 (`.specify/` present)
  was wrong in 1 of 3 runs. S4 (number outgrows the width) was wrong in 3 of 3 runs. The stop
  condition did not apply, so the edit went ahead. The value of the new rule is the overflow case,
  the SpecKit marker and the per-repo settings. It is not basic counting.
- **V3, new text, 3 sessions.** All six scenarios were right in all three runs: S1 `011`, S2 `0004`
  with Digits 4, S3 stop (`.specify/`), S4 stop (overflow), S5 stop (no Digits section), S6 `1001`.
- **V4.** The duplicate number is found by the checklist and repaired by the rename rule, with
  both links resolving.
- **V5.** In a scratch clone, a project generated at `222e96e` and updated to the new files gained
  both files. `bqrs.md` went from 112 to 118 lines, with the pointer. `CLAUDE.md` was byte-identical,
  so it has no new bullet: older projects do not get one (Q7). After the repo set four digits, a
  second update that changed the settings file left the repo's edit alone, with no conflict markers.

**Deviations and findings**

- **Six sessions, not 36.** The plan said three sessions per scenario. Each session answered all
  scenarios in one file, told to treat them as independent repositories. That is cheaper, and one
  session's earlier answers could have influenced its later ones.
- **The baseline had no S5.** Without a settings file there is nothing to be missing. It was run on
  five scenarios, and S2 and S4 gave it no settings value to read.
- **S4 and S5 define "right" by the new rule.** The baseline could not know to stop, so its S4
  failure shows the gap, not a mistake against its own rules.
- **B2 did not reproduce in sessions.** See B2. The checklist and the numeric-comparison rule
  stay, because the failure is real for a "last file name" rule, and it costs two lines.
- **The scorer is a throwaway** in the session scratchpad, not in the repo. It passed a known-good
  answer set and failed a known-bad one before the trials.
- **Not tested:** parallel branches in fresh sessions; SpecKit's own numbering (unverified); the
  next-steps message in `copier.yml` (Q8, left unchanged).
- **This repo's four-digit plans are unchanged** (Q2). Only the template default is three digits.
