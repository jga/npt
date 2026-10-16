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
