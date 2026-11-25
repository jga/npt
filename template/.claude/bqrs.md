# BQRS: the plan shape and the plan review

This file is not imported by `CLAUDE.md`. Read it when you write or review a plan that uses the
BQRS shape. A project that writes plans with another tool does not need it.

## How to review a plan (standing preference)

A review is not finished until the plan carries two things:

1. **Blockers** — anything where a wrong answer produces a system that is quietly *incorrect*,
   not merely suboptimal.
2. **Questions** — what is genuinely undecided, where any answer yields a working system.

**Every blocker and every question gets an explicit recommendation.** Not a survey of options,
not "it depends". A decision should be a *review of a proposal*, not a fresh analysis. Write the
recommendation in the item itself, and copy it into Recommendations (see "One solution, in two
places" below).

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

## Where plans go, and how they are numbered (standing preference)

The location, the numbering, the digits and the file name of a plan are settings of the
repository. Read `.claude/docs/plan_settings.md`, and follow `.claude/plan_numbering.md`, before
you create a plan. Run the checklist in that file before you call a numbered plan finished.
