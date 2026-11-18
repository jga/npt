---
status: done
status_changed: 2026-11-18
type: plan
next: Owner commits and tags (PATCH). Then a new plan if the Sequencing rule needs tightening (see Implementation notes).
---

# Make each blocker and question solution appear in its item and in Recommendations

## Summary

A plan that uses the BQRS shape must write the solution to each blocker and each question in two
places, and both must say the same thing:

1. in the item, directly after the description of the blocker or question; and
2. in the Recommendations section, as an exact copy.

The owner accepts the extra output tokens that the second copy costs.

The fix is a change to one file, `template/.claude/bqrs.md`. It is text only. This plan adds no
script, no test and no tool.

This plan follows its own rule. Each solution below is written once in its item and copied exactly
into Recommendations.

## Motivation

The current `bqrs.md` says Recommendations "restates each open blocker's and question's
recommendation by ID, without re-arguing it". Two plans in this repo were written under that rule.
Both show the defect (counted and read on 2026-11-18):

| Plan | Blocker and question items | Entries in Recommendations | Entry that contradicts its item |
|---|---|---|---|
| 0001_copier_template_repo.md | 12 | 6 | Q4: item says personal account; entry says "an organisation account" |
| 0002_new_project_script.md | 9 | 5 | Entry 4 holds a garbled, duplicated fragment |

Entries are grouped and shortened. After an owner decision, the item is edited and its entry is
not. A reader who reads only Recommendations acts on the wrong solution.

## Scope

In scope: `template/.claude/bqrs.md`, the one file that holds the BQRS rules. It is
template-owned, so `copier update` delivers the change to every generated project.

Not in scope:

- Any code: no script, no test, no tool, no change to `copier.yml` or `scripts/`.
- `template/.claude/conventions.md` and `template/CLAUDE.md.jinja` (Q5).
- Rewriting finished plans (Q3).
- Plan-status rules, and anything about SpecKit.

## Options considered

1. **Keep "restates", add "faithfully".** Rejected. It still allows a summary, and the two
   specimens above were written under that word.
2. **Restate in fewer words, with a rule that the restatement must not add, drop or change a
   decision.** Rejected. No mechanical check exists, and a reader has to judge equality. The
   owner accepts the token cost, so the cheap-to-check option is better.
3. **An exact copy in both places.** Chosen.
4. **Solutions only in Recommendations, with the items pointing to it.** Rejected. It breaks the
   owner's first requirement: the solution follows the item's own presentation.
5. **Solutions only in the items, with Recommendations as a list of IDs and titles.** Rejected.
   The owner requires the aggregate to carry the solutions.
6. **A checking script or test.** Rejected by the owner's scope: no new code.

## Design

All changes are in `template/.claude/bqrs.md`. There are three.

**Change 1.** In "How to review a plan", after the sentence "A decision should be a *review of a
proposal*, not a fresh analysis.", add:

> Write the recommendation in the item itself, and copy it into Recommendations (see "One
> solution, in two places" below).

**Change 2.** Replace the two bullets about Recommendations and Sequencing in "The shape of a
plan (BQRS)", and add the new section "One solution, in two places". The text below is the new
content from the heading "The shape of a plan (BQRS)" to the end of the file. The draft was
checked on 2026-11-18: it is 112 lines in total, it contains none of the banned strings in the
template scrub gate (T5), and its own example passes its own checklist.

`````markdown
## The shape of a plan (BQRS)

A plan's decision part is four sections, in this order: **B**lockers, **Q**uestions,
**R**ecommendations, **S**equencing. They come after the explanatory sections (summary,
motivation, design, scope) and before any dated notes.

- Each blocker carries `[open]` or `[resolved]` on its first line.
- Each blocker and each question ends with its recommendation, in its own section.
- **Recommendations** has one entry per blocker and per question. Each entry is a copy of that
  item's recommendation.
- **Sequencing** says what must land first, what it must not be bundled with, and what can run in
  parallel. It orders the solutions. It never adds or changes one.

## One solution, in two places (standing preference)

Every blocker and every question has one solution: the action the plan recommends or, after the
owner decides, the action the owner chose. Write that solution in two places. Both say the same
thing.

1. **In the item.** It is the last part of the item, after the description of the problem or of
   the undecided point. It starts with `**Recommendation.**`. After an owner decision it starts
   with `**Decision (owner, <date>).**` and replaces the recommendation text.
2. **In Recommendations.** One entry per ID, headed `#### <ID> — <title>` (add `[open]` or
   `[resolved]` for a blocker). The entry holds a copy of the item's solution.

Rules:

- **Copy, do not summarise.** The entry holds the item's text exactly, from the
  `**Recommendation.**` (or `**Decision`) line to the end of the item. Do not shorten, merge,
  reword or reorder it. The extra tokens are accepted. A summary can change the solution. A copy
  cannot.
- **One entry per ID.** Never group IDs in one entry. Resolved blockers and decided questions
  keep their entry.
- **The item is the source.** Write or change the solution in the item first. Copy it to the
  entry in the same edit. After an owner decision, the item and the entry both carry the
  decision.
- **No pointer in place of a solution.** "See Recommendations" or "see B2" is not a
  recommendation. A solution that first appears in Recommendations or Sequencing is a defect.
  Move it into its item.
- **Order.** Put the entries in priority order. The ID identifies an entry, not its position.

Before you call a plan finished:

1. Count the headings that start `### B` or `### Q`. Count the headings that start `#### B` or
   `#### Q` in Recommendations. The two counts are equal.
2. For each ID, read the item's solution and the entry side by side. They are identical.
3. Search Recommendations and Sequencing for an action that is not in an item. There is none.

Example, with one blocker and one question:

```
## Blockers

### B1 — Retries can charge a card twice [open]

`charge()` calls the gateway again after a timeout. The first call may have succeeded.

**Recommendation.** Send an idempotency key with each charge. Reuse the same key on every retry
of that charge.

## Questions

### Q1 — Retry limit

**Recommendation.** Three retries, with waits of 1 s, 2 s and 4 s.

## Recommendations

#### B1 — Retries can charge a card twice [open]

**Recommendation.** Send an idempotency key with each charge. Reuse the same key on every retry
of that charge.

#### Q1 — Retry limit

**Recommendation.** Three retries, with waits of 1 s, 2 s and 4 s.
```
`````

**Change 3.** None to `conventions.md`, `CLAUDE.md.jinja` or any other file (Q5).

Two details of the rule:

- The "solution" is the text from the `**Recommendation.**` or `**Decision` line to the end of the
  item. The description of the problem stays only in the item. So an entry is short, and a plan's
  aggregate stays readable.
- Entries use `####` headings and items use `###` headings, so a count of one kind never includes
  the other.

## Verification

No new code. These are manual checks, with the existing test suite as a guard.

| ID | Check | Negative control |
|---|---|---|
| V1 | The edit changes only `template/.claude/bqrs.md`. `wc -l` on it is at most 120. The existing suite still passes: `uv run --with copier==9.19.1 --with pytest pytest -q tests` (53 tests). This covers T5 (scrub gate over `template/`) and T8 (`bqrs.md` linked, not imported; `conventions.md` free of "Blockers"). | The suite's own controls stand. Nothing new is added. |
| V2 | Apply the new checklist to 0001 and 0002. Expected: both fail. Neither has `####` entries. By ID they have 6 and 5 entries for 12 and 9 items, and 0001 Q4 differs. Then apply it to this plan: it passes (10 items, 10 entries, each pair identical). | A known-bad plan (0001) must fail the checklist. |
| V3 | A trial in a fresh Claude session. Give it only the new `bqrs.md` and a fixed brief: three blockers and three questions about a small feature. Ask for a BQRS plan. Pass if the counts are equal, every pair is identical, and no solution is only in Recommendations or Sequencing. Then tell it that the owner decided one question differently. Pass if the item and its entry both change to the same `**Decision (owner, <date>).**` paragraph. Run it three times. | Run the same brief three times with the old `bqrs.md` (the version at commit `75f4499`). The old text is expected to produce at least one mismatch. If all three runs pass the same checks, stop: the cause is not in `bqrs.md`. |
| V4 | Generate a project at commit `75f4499`. Run `copier update` to the new commit. Only `.claude/bqrs.md` changes, and `CLAUDE.md` is byte-identical. | The mechanism is already covered by T2; this checks it on real content once. |

## Blockers

### B1 — The Recommendations entry can differ from the item's solution [resolved]

Resolved 2026-11-18. `bqrs.md` now requires an exact copy. V3: 18 of 18 solutions in the new-text runs are verbatim in their entries. 0 of 18 are verbatim in the old-text runs.

The current rule in `.claude/bqrs.md` says Recommendations "restates each open blocker's and
question's recommendation by ID, without re-arguing it". "Restates" allows shortening and
rewording. A short version can change the solution, and a reader of Recommendations then acts on
the changed one.

Observed 2026-11-18. In 0001_copier_template_repo.md, Q4 in its own section reads "Decision
(owner, 2026-10-15). The repo lives under the personal account", but its entry in Recommendations
says "an organisation account". In 0002_new_project_script.md, entry 4 in Recommendations holds a
garbled, duplicated fragment ("name is the directory name (Q2 is decided …); name is the
directory name; …").

**Recommendation.** In `.claude/bqrs.md`, replace "restates" with a copy rule. Each entry in
Recommendations is an exact copy of its item's solution, from the `**Recommendation.**` or
`**Decision` line to the end of the item. Say that a summary, a merge and a reword are all
forbidden, and that the extra tokens are accepted.

### B2 — Resolved items and owner decisions leave the aggregate behind [resolved]

Resolved 2026-11-18. V3 phase 2: after an owner decision on Q2, 3 of 3 runs changed the item and its entry to the same `**Decision (owner, 2026-11-18).**` paragraph and left the other five pairs unchanged.

The current rule covers only "open" items, and says nothing about editing. After an owner decision
or a resolution, the author edits the item and does not edit the aggregate. That is how the 0001
Q4 mismatch above came about. The resolved blockers B1 and B4 in 0001 also keep a shortened entry
that is not the text of their item.

**Recommendation.** Every blocker and every question has an entry, resolved and decided items
included. The item is the source: change the item first, then copy it to its entry, in the same
edit. An owner decision replaces the recommendation text in the item with a
`**Decision (owner, <date>).**` paragraph, and the entry copies that paragraph.

### B3 — Grouped entries drop solutions [resolved]

Resolved 2026-11-18. V3 new-text runs: 6 items and 6 entries in 3 of 3 runs. Grouping did not occur in V3 even with the old text. The rule stays because 0001 and 0002 did group.

Counted 2026-11-18. 0001_copier_template_repo.md has 12 blocker and question items and 6 numbered
entries in Recommendations. 0002_new_project_script.md has 9 items and 5 entries. Six questions
in 0001 share one line of about 20 words. One line cannot carry six solutions, so the detail of
each is lost.

**Recommendation.** One entry per ID. Never group IDs. Add a completion check to
`.claude/bqrs.md`: count the `### B` and `### Q` headings in the item sections, count the `#### B`
and `#### Q` entry headings in Recommendations, and require equal counts.

### B4 — The current text does not say where an item's recommendation goes [resolved]

Resolved 2026-11-18. In V3, 6 of 6 runs (old and new text) put the solution in the item. The placement risk was not observed in V3 with either text. The rule stays because the owner asked for it and the old text did not state it.

`.claude/bqrs.md` says every blocker and question "gets an explicit recommendation". It does not
say where. An author could put every solution only in Recommendations and leave each item as a
problem statement. A reader of an item would then have to find its solution in another section.
This has not happened in 0001 or 0002. The text simply does not forbid it.

**Recommendation.** Add to `.claude/bqrs.md`: the solution is the last part of the item, after the
description of the problem, and starts with `**Recommendation.**`. A pointer such as "see
Recommendations" does not count. A solution that first appears in Recommendations or Sequencing
is a defect, and moves into its item.

## Questions

### Q1 — Copy exactly, or restate in fewer words

The owner accepts extra output tokens to write each solution in two places, and requires that the
two say the same thing. There are two ways to get "the same".

**Decision (owner, 2026-11-18).** Copy exactly. The owner accepts the extra tokens, and an exact copy can be
checked by reading two texts side by side. A shorter restatement needs a judgement that the two
say the same thing, and the specimens above show that judgement failing.

### Q2 — Which copy is the source

When the two copies differ, one of them is wrong. The rule must say which one.

**Decision (owner, 2026-11-18).** The item. It sits next to the evidence. The entry in Recommendations is the
copy, and is redone whenever the item changes.

### Q3 — Do the two existing plans get fixed

0001 and 0002 were written under the old rule. 0001 has one entry that contradicts its item (Q4).
0002 has one garbled entry (4). Both have grouped, shortened entries that are lossy but not wrong.

**Decision (owner, 2026-11-18).** Fix only what is wrong, not what is merely short. Correct the 0001 Q4 entry
and the garbled 0002 entry 4, each as a dated correction, in a separate change after this one.
Leave the grouped one-line entries. Both plans are done, and rewriting them to the new rule would
retrofit finished documents.

### Q4 — How long bqrs.md may grow

The draft in Design is 112 lines. The current file is 44 lines.

**Decision (owner, 2026-11-18).** Accept the growth, and cap the file at 120 lines. The file is linked from
`CLAUDE.md`, not imported, so it costs context only when a task reads it. If the rule needs more
than the cap, split the rule into its own file.

### Q5 — Do conventions.md and CLAUDE.md.jinja change

Both are under `.claude/` or point at it, and both mention plans in some way.

**Decision (owner, 2026-11-18).** No. `conventions.md` is imported on every task, and test T8 keeps BQRS text
out of it (it fails if the word "Blockers" appears). `CLAUDE.md` is project-owned after the first
copy, so a change there would not reach existing projects. `bqrs.md` is template-owned, so
`copier update` delivers the new rule to every project.

### Q6 — How the rule is checked with no new code

The owner limits this plan to `bqrs.md` and other `.claude` items. It must not lead to new code.

**Decision (owner, 2026-11-18).** A written checklist at the end of the rule (count the headings, compare each
pair, search for stray solutions), and a trial in a fresh Claude session (see Verification). No
script, no test, no tool. The existing test suite still runs, to show that the edit broke
nothing.

## Recommendations

In priority order. Each entry is a copy of the solution in its item.

#### B1 — The Recommendations entry can differ from the item's solution [resolved]

**Recommendation.** In `.claude/bqrs.md`, replace "restates" with a copy rule. Each entry in
Recommendations is an exact copy of its item's solution, from the `**Recommendation.**` or
`**Decision` line to the end of the item. Say that a summary, a merge and a reword are all
forbidden, and that the extra tokens are accepted.

#### B3 — Grouped entries drop solutions [resolved]

**Recommendation.** One entry per ID. Never group IDs. Add a completion check to
`.claude/bqrs.md`: count the `### B` and `### Q` headings in the item sections, count the `#### B`
and `#### Q` entry headings in Recommendations, and require equal counts.

#### B2 — Resolved items and owner decisions leave the aggregate behind [resolved]

**Recommendation.** Every blocker and every question has an entry, resolved and decided items
included. The item is the source: change the item first, then copy it to its entry, in the same
edit. An owner decision replaces the recommendation text in the item with a
`**Decision (owner, <date>).**` paragraph, and the entry copies that paragraph.

#### B4 — The current text does not say where an item's recommendation goes [resolved]

**Recommendation.** Add to `.claude/bqrs.md`: the solution is the last part of the item, after the
description of the problem, and starts with `**Recommendation.**`. A pointer such as "see
Recommendations" does not count. A solution that first appears in Recommendations or Sequencing
is a defect, and moves into its item.

#### Q1 — Copy exactly, or restate in fewer words

**Decision (owner, 2026-11-18).** Copy exactly. The owner accepts the extra tokens, and an exact copy can be
checked by reading two texts side by side. A shorter restatement needs a judgement that the two
say the same thing, and the specimens above show that judgement failing.

#### Q2 — Which copy is the source

**Decision (owner, 2026-11-18).** The item. It sits next to the evidence. The entry in Recommendations is the
copy, and is redone whenever the item changes.

#### Q6 — How the rule is checked with no new code

**Decision (owner, 2026-11-18).** A written checklist at the end of the rule (count the headings, compare each
pair, search for stray solutions), and a trial in a fresh Claude session (see Verification). No
script, no test, no tool. The existing test suite still runs, to show that the edit broke
nothing.

#### Q5 — Do conventions.md and CLAUDE.md.jinja change

**Decision (owner, 2026-11-18).** No. `conventions.md` is imported on every task, and test T8 keeps BQRS text
out of it (it fails if the word "Blockers" appears). `CLAUDE.md` is project-owned after the first
copy, so a change there would not reach existing projects. `bqrs.md` is template-owned, so
`copier update` delivers the new rule to every project.

#### Q3 — Do the two existing plans get fixed

**Decision (owner, 2026-11-18).** Fix only what is wrong, not what is merely short. Correct the 0001 Q4 entry
and the garbled 0002 entry 4, each as a dated correction, in a separate change after this one.
Leave the grouped one-line entries. Both plans are done, and rewriting them to the new rule would
retrofit finished documents.

#### Q4 — How long bqrs.md may grow

**Decision (owner, 2026-11-18).** Accept the growth, and cap the file at 120 lines. The file is linked from
`CLAUDE.md`, not imported, so it costs context only when a task reads it. If the rule needs more
than the cap, split the rule into its own file.

## Sequencing

1. **First, and before any edit:** the owner decides Q1 to Q6. B1 to B4 shape the new text.
2. **Then, before editing `bqrs.md`:** run the baseline half of V3, three runs with the old text.
   If all three pass the same checks, stop and revisit B1 to B4.
3. **Then:** one change that edits only `template/.claude/bqrs.md`, as in Design. Run V1 and
   check that the file is at most 120 lines. Add one `CHANGELOG.md` line. Tag it as a PATCH, as
   Q5 in 0001_copier_template_repo.md says for text fixes.
4. **Then:** the other half of V3 (three runs with the new text), V2 and V4.
5. **Then, as a separate change:** the dated corrections in 0001 and 0002 from Q3.
6. **Must not be bundled with:** a change to `conventions.md` or `CLAUDE.md.jinja`, any code or
   test, the adoption mode, or the plan-status and SpecKit questions. They are different
   decisions with different failure modes.

## Implementation notes (2026-11-18)

The edit is in `template/.claude/bqrs.md` (44 lines became 112), with one `CHANGELOG.md` line.
Nothing else in `template/`, `scripts/` or `tests/` changed. The owner commits and tags.

**Results**

- **V1.** The existing suite gives 53 passed. The diff against `HEAD` touches only `bqrs.md`,
  `CHANGELOG.md` and this plan.
- **V2.** A throwaway checker (kept in the session scratchpad, not in the repo) applies the
  checklist. It passes this plan (10 items, 10 entries, each pair identical). It fails 0001 and
  0002 (no `####` entries; 6 of 12 and 5 of 9 IDs listed; grouped lines).
- **V3 baseline, old text, 3 runs.** All 18 solutions were shortened. No entry was verbatim. Entries
  were 17% to 41% of the length of the solution they stand for (mean 29%). They dropped steps,
  for example how to compute `Retry-After`, the test to write, and the ticket to open. So the stop
  condition did not apply, and the edit went ahead.
- **V3 new text, 3 runs.** All three passed: 6 items, 6 `####` entries, every solution labelled
  and verbatim in its entry, no grouped entry.
- **V3 phase 2, 3 runs.** The owner decided Q2 differently (503 with `Retry-After`, not 429). In 3
  of 3 runs the Q2 item and its entry both became the same `**Decision (owner, 2026-11-18).**`
  paragraph, and the other five pairs were unchanged.
- **V4.** In a scratch clone, a project generated at `75f4499` was updated to a commit that holds
  the new `bqrs.md`. Only `.claude/bqrs.md` changed. `CLAUDE.md` was byte-identical.

**Findings**

- **One stray in Sequencing.** In 1 of 3 new-text runs, Sequencing said "ship the limit of 60 with
  the logging". Logging appears nowhere in that run's Q1 item. That is an action first appearing in
  Sequencing, which the rule forbids, and checklist step 3 would catch it. The other two runs had
  none. I made no text change. If it recurs, tighten the Sequencing rule in a new plan.
- **The old baseline is partly a matter of definition.** The old rule asked for a "restatement",
  so a strict verbatim test fails it by construction. The length and dropped-step figures are the
  evidence that the content was lost, not only the wording.
- **A deviation by a trial session.** In phase 2, one session used two `Edit` calls where I had
  allowed only `Read` and `Write`. It said so. The result is the same.
- **The checker was wrong twice and was fixed twice, with the known plans as controls.** It
  first missed bullet-style items, and it first flagged a copied solution that mentions another
  ID. After each fix it still passed this plan and failed 0001 and 0002.
- **My own edit of this plan had a bug, found by reading it.** I first split the file at the
  first "## Blockers", which is inside the Design example, so the example was edited and two real
  items were not. The checker did not see it, because it ignores fenced blocks. I restored the file
  and redid the edit at the right heading. Lesson: the checker proves the structure, not that the
  Design example still matches `bqrs.md`.
- **Q3 corrections.** The two wrong entries are corrected in 0001 and 0002 as dated corrections,
  in separate edits from the `bqrs.md` change.

**The brief used for V3** (`brief.md`, given to each session with the rules file):

````markdown
# Brief

Feature: add a per-user rate limit to an internal HTTP API. The endpoint is `GET /v1/export`.
The service runs as 3 replicas behind a load balancer. Users are identified by the `X-User-Id`
request header.

Write the decision part of a BQRS plan for this feature: the four sections `## Blockers`,
`## Questions`, `## Recommendations` and `## Sequencing`, in that order. Follow the rules in the
BQRS file you were given. You choose the recommendations.

Use exactly these six items, with these IDs, in this order.

Blockers (a wrong answer makes the system quietly incorrect):

- **B1** — The request counter is kept in process memory. With 3 replicas, each replica counts
  separately, so a user can make 3 times the intended number of requests.
- **B2** — The counter resets at the start of each clock minute. A user can send the full limit
  at 12:00:59 and the full limit again at 12:01:00, so twice the limit in two seconds.
- **B3** — A request with no `X-User-Id` header is counted under one shared key, "anonymous". One
  anonymous caller can use up the limit for every anonymous caller.

Questions (any answer gives a working system):

- **Q1** — What limit per user: 60 requests per minute, or 120.
- **Q2** — What response when the limit is exceeded: HTTP 429 with a `Retry-After` header, or
  HTTP 503.
- **Q3** — Whether requests to the health check `/healthz` count toward the limit.

Output only the markdown of the four sections. Do not add a title or any other section.
````
