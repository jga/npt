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
