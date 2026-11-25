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
