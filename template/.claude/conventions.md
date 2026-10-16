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

- A code-based feature change gets one thing by default: one line in `journal/CHANGELOG.md` that
  links to it. Nothing else.
- A change earns a line in `CLAUDE.md` or this file only if it states a reusable rule a
  *future, unrelated* task must apply. Test it with the blocker question: would getting this
  wrong later be quietly incorrect, or only a missed chance to know history? Only the first
  belongs here.
- Target size for `CLAUDE.md`: under about 300 lines. If it grows past that, audit before adding.
