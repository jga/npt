---
status: done
status_changed: 2026-11-18
type: plan
next: None. Later work is a new plan: adoption mode (B3 in 0001_copier_template_repo.md) and a non-empty lowercase readme.md (Q4 here).
---

# A bootstrap script that creates or adopts a project from the npt template

## Summary

This plan adds one bash script to the `npt` repo, `scripts/new-project.sh`. One command takes a
directory from "new or bare" to "project with the template applied":

```
new-project.sh <project-name> [<commit-sha>] [-- <copier args>...]
```

- `<project-name>` is required. It is the directory name and the `project_name` answer.
- `<commit-sha>` is optional. If it is missing, the script uses the latest commit on `main`. It
  prints the full SHA, and passes that SHA to Copier. It never passes the word `main`.

The script serves two use cases:

1. **A new project.** The directory does not exist. The script creates it.
2. **A bare or minimal directory.** The directory exists and holds some files, but has no
   `pyproject.toml`. The script applies the template, then runs `uv init`. Existing files stay.

The repo `README.md` is rewritten to explain: how to set the script up, what is in it, how
`uvx copier` works, and the same steps by hand for anyone who does not want the script.

This plan replaces the first version of 0002, which only added a pre-step to the usage text so
that an empty `README.md` is filled. That feature is now one step inside the script.

## Motivation

The usage text in `README.md` says: run `uv init`, then `copier copy`. Three problems follow from
that order. All three were reproduced on 2026-11-18 (Copier 9.19.1, uv 0.12.23, Linux), against
the template at commit `33615e3` or this repo's working tree:

- **An empty README stays empty.** `uv init` makes a `README.md` with 0 bytes. `README.md` is in
  `_skip_if_exists`, so Copier skips it. The project ends with an empty README.
- **The template `.gitignore` is skipped.** `uv init` also writes a `.gitignore`, with Python
  entries only. `.gitignore` is in `_skip_if_exists`, so the template version is never written.
  The result has 0 lines for `.env` and 0 lines for `.claude/settings.local.json`. The security
  table in 0001_copier_template_repo.md says the generated `.gitignore` covers both. That claim
  is false in the documented flow.
- **A lowercase `readme.md` gives two READMEs.** An empty `readme.md` stays, and Copier writes a
  second `README.md` (472 bytes) beside it.

The same facts hold in the other order. Running `copier copy` first, then `uv init .`, gave:
`README.md` is the template README (475 bytes), `.gitignore` has the `.env` lines, and
`pyproject.toml` has `name = "newp"` from the directory name. `uv init` does not overwrite
existing files. It left a `README.md`, a `main.py` and a `.gitignore` with content unchanged.

## Scope

In scope: `scripts/new-project.sh`, its tests, a shellcheck step in CI, the `README.md` rewrite,
one `CHANGELOG.md` line.

Not in scope:

- Any change to `copier.yml` or to `template/`. The script lives outside `template/`, so Copier
  never copies or runs it.
- Windows shells. The script is bash. WSL works. `uv` and `copier` themselves are cross-platform.
- macOS. The script avoids bash 4 features where that costs nothing, but CI runs Linux only, so
  macOS is untested.
- Adoption of a project that already has a `pyproject.toml` and its own `CLAUDE.md`. That is the
  adoption mode in B3 of 0001_copier_template_repo.md. The script handles an existing
  `pyproject.toml` only by skipping `uv init`.

## Options considered

1. **A `_tasks` entry in `copier.yml`.** Rejected. Any `_tasks` entry makes every consumer pass
   `--trust` (B1 in 0001_copier_template_repo.md).
2. **An answer that switches `README.md` out of `_skip_if_exists`.** Rejected. Tested: Copier
   renders the entry, so the switch works. But Copier cannot read the file. With the answer true
   and `--overwrite`, a README with content (14 bytes) was replaced by the template README (472
   bytes). Copier also saves the answer, and `copier update` reuses saved answers (reasoned, not
   tested).
3. **Change only the documented order: `copier copy` first, then `uv init .`.** Works for a new
   project. It fixes the empty README and the `.gitignore`, with no script. It does not help an
   existing directory with its own empty README or its own `.gitignore`, and it does not give a
   default SHA.
4. **A pre-step snippet in the README.** The first version of this plan. Superseded by item 5.
5. **A script outside `template/`.** Chosen by the owner. It carries the order fix from item 3,
   plus the checks the other options cannot do. The cost is code that the consumer runs from a
   public repo (B3).

## Design

### Setup, as the README will say it

```bash
mkdir -p ~/.local/bin
curl -fsSL https://raw.githubusercontent.com/jga/npt/<commit-sha>/scripts/new-project.sh \
  -o ~/.local/bin/npt-copier
less ~/.local/bin/npt-copier          # read it before you run it
chmod +x ~/.local/bin/npt-copier
```

The URL names a commit, not `main`, so the file cannot change after you read it. The script needs
`bash`, `git` and `uv` (which provides `uvx`). It checks for them at the start.

### Usage, as the README will say it

```bash
npt-copier my-project                    # new project, latest main
npt-copier my-project 33615e3            # new project, a chosen commit
npt-copier existing-dir                  # bare or minimal directory with some content
npt-copier my-project -- --defaults --data one_line_description="A demo"   # no prompts
```

Copier asks the remaining questions (description, language, source directory). Everything after
`--` goes to `copier copy` unchanged. The script never passes `--overwrite`.

### What the script does, in order

1. **Check the arguments.** The name must match `^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$`. This also
   meets the `project_name` rule in `copier.yml` (1 to 80 characters, no braces, no percent sign,
   no newline). A SHA, if given, must match `^[0-9a-f]{7,40}$`. Bad input exits with code 2
   before anything is created.
2. **Check the tools.** `git` and `uv` must be on `PATH`.
3. **Check the target, read-only.** A target that is a symlink, or exists and is not a
   directory, exits with code 2. This runs before any network call.
4. **Resolve the SHA, then find the target.** If no SHA was given, run
   `git ls-remote "$NPT_REPO_URL" refs/heads/main`. If the ref is missing, stop. The script does
   not fall back to `HEAD` or `master`. Print the full SHA. Only then: the directory does not
   exist, so create it (use case 1), or it exists, so use it (use case 2).
5. **Remove empty README files.** In the target directory only, delete a README file (any case)
   that is a regular file, not a symlink, readable, and has no non-whitespace character. `grep`
   runs with `LC_ALL=C`, so only ASCII whitespace counts as empty.
6. **Warn about other README files.** If `README.md` does not exist and another README file is
   kept (`readme.md`, `README.rst`, `README`), the script prints that Copier will add `README.md`
   beside it (Q4).
7. **Apply the template.**
   `uvx --from copier==9.19.1 copier copy --data project_name="$NAME" "$NPT_REPO_URL" . --vcs-ref "$SHA" [extra args]`.
   `$NPT_REPO_URL` defaults to `https://github.com/jga/npt.git`. Tests set it to a local repo.
8. **Protect secrets in `.gitignore`.** If `.gitignore` lacks the exact lines `.env`, `.env.*` or
   `.claude/settings.local.json`, append them and print what was added. Nothing is removed or
   reordered. For a new project the template `.gitignore` already has them, so nothing happens.
9. **Run `uv init`.** If `pyproject.toml` is absent, run `uv init --no-workspace .`. If it is
   present, skip it and say so. `--no-workspace` stops `uv` from adding the new project to a
   parent directory's workspace.
10. **Print a summary.** The directory, the full SHA (to record in the consumer's notes), and a
    reminder that `copier update` needs a git repository. `uv init` creates one when none exists.

If step 7 fails and the script created the directory in step 4, it runs `rmdir` on it. `rmdir`
removes only an empty directory, so it cannot delete content.

The file is organised as small functions (`usage`, `die`, `validate_name`, `validate_sha`,
`resolve_sha`, `remove_empty_readmes`, `warn_other_readmes`, `ensure_gitignore_lines`, `main`).
`main` runs only when the file is executed, not when it is sourced. Tests source the file and
call the functions directly.

### How `uvx copier` works, as the README will say it

- `uvx` runs a Python tool in a throwaway environment. Nothing is installed globally. The script
  pins `copier==9.19.1`, the version the tests ran against.
- `copier copy <url> <dest> --vcs-ref <sha>` clones the repo into a temp directory, checks out the
  SHA, and reads `copier.yml`. `_subdirectory: template` means only `template/` is rendered.
- Copier asks the questions in `copier.yml`, renders files whose names end in `.jinja`, and copies
  the others byte for byte.
- A file in `_skip_if_exists` is written only if it does not exist yet. That protects your
  `CLAUDE.md`, `README.md` and `.gitignore`.
- Copier writes `.copier-answers.yml` with the answers and the commit (`_commit`). Observed: a
  full SHA is stored in the short form (`33615e3`).
- Later, `uvx copier update --vcs-ref <sha>` reads that file, and does a three-way merge. It needs
  a clean git working tree.
- Without `--vcs-ref`, Copier uses the latest git tag, or `HEAD` when there are no tags. Observed:
  "No git tags found in template; using HEAD as ref". The script always passes a SHA.

### The same steps by hand, as the README will say it

```bash
mkdir my-project && cd my-project
uvx --from copier==9.19.1 copier copy https://github.com/jga/npt.git . --vcs-ref <commit-sha>
uv init --no-workspace .
```

Copier goes first. That order is the one that keeps the template `.gitignore` and `README.md`.

### Behaviour of the empty-README step

Tested on 2026-11-18 with this loop, under `dash` (`sh -e`) and `bash -e`. Every row exits 0.

```bash
for f in [Rr][Ee][Aa][Dd][Mm][Ee].md; do
  if [ -f "$f" ] && [ ! -L "$f" ] && [ -r "$f" ] && ! grep -q '[^[:space:]]' "$f"; then
    rm -- "$f"
  fi
done
```

| Case | After the step |
|---|---|
| `README.md` with 0 bytes | Removed. |
| `README.md` with only spaces, tabs and newlines | Removed. |
| `readme.md` or `Readme.md` with 0 bytes | Removed. |
| Empty `readme.md` and a `README.md` with content | Empty one removed. Content file kept. |
| `README.md` with content, one character, or only `<!-- todo -->` | Kept. |
| `README.md` with binary bytes, or only a UTF-8 byte-order mark | Kept. |
| `README.md` is a symlink, a directory, or has mode `000` | Kept. |
| No README file | Nothing happens. |

The first draft of this loop used an `&&` chain without `if`. When the last file did not match,
the loop exited 1, and `step && next-step` would not run `next-step`. The `if … fi` form exits 0
in every row.

### Tested flow of the script's order

New directory: `copier copy`, then `uv init --no-workspace .`. Result: template `README.md`, a
`.gitignore` with `.env`, `settings.local.json` and `__pycache__` entries, and `pyproject.toml`.

Existing directory with `notes.txt`, a `.gitignore` containing `mine.log`, and an empty
`README.md`: the empty README is removed, then Copier and `uv init` run. Result: `notes.txt`
unchanged, `README.md` is the template README, and `.gitignore` is still only `mine.log`. The
template `.gitignore` was skipped, which is why step 8 exists (B1).

Existing directory with a `pyproject.toml`: `uv init .` exits 2 with "Project is already
initialized". The script checks for the file first (step 9).

## Security

The script is code that the consumer runs, from a public repo. That is a change from 0001, whose
security model says the template ships no script. The template still ships none: the script is
outside `template/`, so Copier never copies or runs it, and `--trust` is still not needed.
B3 lists the controls.

Two points about the default SHA:

- The default takes whatever `main` is at that moment. The consumer has not reviewed it. The
  template text is instructions to Claude (`CLAUDE.md`, `conventions.md`), so a bad commit on
  `main` would steer Claude in every project made that day. A pinned SHA protects only against a
  change between review and use.
- The script prints the full SHA, and Copier records `_commit`. The consumer can see exactly what
  was used and can pin it next time.

## Verification

Tests go in `tests/test_generate.py` and run in the existing `generate` CI job. They use a
temporary git repo built from the working tree as `NPT_REPO_URL`, so they do not use the
network. They run the script with `-- --defaults --data one_line_description=x`. IDs start with
N so they do not clash with T1 to T10 in 0001_copier_template_repo.md.

| ID | Test | Negative control |
|---|---|---|
| N1 | `new-project.sh NAME SHA` in an empty parent directory. The directory has the template files and `pyproject.toml`. `README.md` starts with `# NAME`. `.gitignore` has `.env` and `.claude/settings.local.json`. `_commit` in `.copier-answers.yml` starts with the SHA. | Run the old order (`uv init`, then `copier copy`) in a scratch directory. `README.md` must stay at 0 bytes and `.gitignore` must lack `.env`. This pins the defect; if it changes, the test fails. |
| N2 | An existing directory with `notes.txt`, a `.gitignore` containing `mine.log`, and an empty `README.md`. After the script: `notes.txt` is byte-identical, `README.md` is the template README, `.gitignore` still starts with `mine.log` and now has the three secret lines, and `pyproject.toml` exists. | Same directory with a `README.md` that has content. It must be byte-identical afterwards. |
| N3 | An existing `readme.md` with content. It is kept byte-identical, `README.md` is added beside it, and the warning is printed. | — |
| N4 | No SHA given, and the test repo has two commits. `_commit` is the tip of `main`. | Pass the older SHA. `_commit` must be the older one. |
| N5 | No arguments, a bad name (`../x`, `a b`, `-x`, 81 characters), a bad SHA (`zzzzzzz`, `abc`), or a target that is a file: exit 2, and nothing is created. | — |
| N6 | An existing `pyproject.toml`: the script exits 0, skips `uv init`, and leaves the file byte-identical. | Plain `uv init .` in the same directory must fail. This pins the premise. |
| N7 | The test repo has no `refs/heads/main` (branch `trunk`) and no SHA is given: exit non-zero, and no directory is created. | — |
| N8 | A well-formed SHA that does not exist (`deadbeefdeadbeef`): exit non-zero, and the directory the script created is gone. | Same run into a directory that already existed with a file in it. The directory and file must remain. |
| N9 | The empty-README cases in the table above, by sourcing the script and calling `remove_empty_readmes`. Check which files remain and that the exit code is 0. | Replace the `grep` test with `true`. The "content is kept" rows must then fail. |
| N10 | `shellcheck` passes on `scripts/new-project.sh`. A grep gate finds no `eval`, no `curl` and no `sh -c` in it. | Plant `eval "$1"` in a scratch copy. The gate must fail. |
| N11 | `README.md` names `scripts/new-project.sh` and `npt-copier`, does not name `npt-new`, and the script file is executable. | — |

The first GitHub run of the script (real `git ls-remote` and a real clone over https) is a manual
step, because the tests use a local repo. The owner runs the three cases once by hand after the
change is on `main`.

## Blockers

### B1 — The documented flow silently drops the secret entries from `.gitignore` [resolved]

Resolved 2026-11-18. The script runs Copier before `uv init` and appends missing lines (step 8). N1
and N2 pass. N1 also checks that nothing was appended for a new project; that assertion killed a
mutation that ran `uv init` first. 0001_copier_template_repo.md has the dated correction. The
original text follows.

Reproduced: `uv init`, then `copier copy`, leaves a `.gitignore` with no `.env` line and no
`.claude/settings.local.json` line. The consumer sees no error. A local settings file or an `.env`
file can then be committed. 0001_copier_template_repo.md claims the opposite in its security
table.

**Recommendation.** Two parts. For a new project, run Copier before `uv init`, so the template
`.gitignore` is written (tested above). For an existing directory that has its own `.gitignore`,
append the three missing lines and print them (step 8). N2 tests it, including a `.gitignore`
with no trailing newline. Add a dated note to 0001_copier_template_repo.md that its `.gitignore` claim holds
only in this order.

### B2 — The script deletes files, so a wrong "empty" test loses user content [resolved]

Resolved 2026-11-18. N2 and N9 pass. A mutation that replaced the `grep` condition with `true`
made N9 fail on the content cases, so the control checks the right thing. The original text
follows.

Step 5 runs `rm`. If the test treats a file with content as empty, the consumer's README is gone
with no undo. Step 7 can also change files if the script ever passes `--overwrite`.

**Recommendation.** Delete only a regular, non-symlink, readable file with no non-whitespace
character. Treat every unclear case as content (binary, byte-order mark only, comment only). Use
the loop tested above. Never pass `--overwrite`. N2 and N9 hold the line, each with a negative
control. For a file Copier would change, Copier asks per file when it has a terminal, and keeps
the file when it has none (the second behaviour was observed for `README.md`; the first is
Copier's documented behaviour and was not run).

### B3 — The script is code that runs on the consumer's machine, from a public repo [resolved]

Resolved 2026-11-18, after the owner committed `75f4499` to `main`. The README setup step was run
as written, with that SHA. The original text follows.

A bad version of this file runs with the consumer's rights. A moved ref, a compromised account,
or a bad edit would reach everyone who runs it. 0001_copier_template_repo.md treats this class of
risk as the main one.

**Recommendation.** Controls, each with a test or a check:

- The README tells the consumer to download the script by commit SHA, and to read it first.
- The script is short, has no `eval`, no `curl`, no `sh -c`, and quotes every variable (N10).
- Every argument is checked against a pattern before use (N5). The name and SHA never reach a
  shell as code.
- The only network use is `git ls-remote` and `uvx` with a pinned `copier==9.19.1`.
- The branch protection, tag protection, 2FA, and SHA-pinned CI actions listed in
  0001_copier_template_repo.md apply to this file too. `shellcheck` runs inside N10, so the
  existing `generate` CI job covers it.
- The scrub gate (T5 in 0001_copier_template_repo.md) is extended to `scripts/`.

Status 2026-11-18: every control above is built and tested. The three cases ran by hand against
real GitHub, and the SHA-pinned download was tried (see Implementation notes).

## Questions

### Q1 — Script or pre-step

**Decision (owner, 2026-11-18).** A script. This replaces the first version of this plan, which
recommended a pre-step in the README. B3 records the cost.

### Q2 — Name and place of the script

**Decision (owner, 2026-11-18).** The installed command is `npt-copier`, not `npt-new`. The file
in the repo stays `scripts/new-project.sh`. The README tells the consumer to install it as
`npt-copier`. `scripts/` is outside `template/`, so Copier does not see it.

### Q3 — Does the name argument double as the directory name

**Recommendation.** Yes, with the pattern in step 1. One argument, one meaning. A name with
spaces is not allowed, because it would also have to be a safe directory name. The README says so.
A different human-readable title can be set later in `README.md`.

### Q4 — A non-empty `readme.md` that is not `README.md`

Copier writes `README.md` beside it (observed for an empty one; the same rule applies). `README.rst`
and a bare `README` have the same effect.

**Recommendation.** Warn and continue (step 6). Do not rename or merge the consumer's file. A
full answer belongs to the adoption mode in B3 of 0001_copier_template_repo.md.

### Q5 — Which branch is "latest"

**Recommendation.** Only `main`. If `refs/heads/main` does not exist, stop with an error. A
fallback to `HEAD` or `master` would guess.

### Q6 — Prompts and passthrough

**Recommendation.** The script asks no questions itself. Copier asks the rest. Arguments after
`--` pass through to `copier copy`, so tests and scripted use can supply `--defaults` and
`--data`. This is the one place where a consumer can pass `--overwrite` on purpose, and the
README says what it does.

## Recommendations

In priority order. Reasoning is under each ID above.

1. **B1** — Copier before `uv init`. Append the missing secret lines to an existing `.gitignore`.
   Add a dated note to 0001_copier_template_repo.md. N1 and N2.
2. **B2** — Delete only provably empty regular files. Never pass `--overwrite`. N2 and N9.
3. **B3** — Pin the script by commit SHA, keep it small and `eval`-free, validate every argument,
   pin `copier`, run `shellcheck`, extend the scrub gate to `scripts/`. N5 and N10.
4. **Q3, Q4, Q5, Q6** — name is the directory name (Q2 is decided: installed as `npt-copier`); name is the
   directory name; warn on other README files; `main` only; passthrough after `--`.
5. **Q1, Q2** — Decided: a script, installed as `npt-copier`.

## Sequencing

1. **First, and before any code:** the owner approves B1 to B3 and Q2 to Q6. They shape the
   script and the README.
2. **Then:** build the script and tests N1 to N11 as one change. Tag it
   as a MINOR, because it adds a new file (Q5 in 0001_copier_template_repo.md). Add one
   `CHANGELOG.md` line.
3. **Then:** rewrite the `README.md` usage text to match (setup, usage, what the script does, how
   `uvx copier` works, the by-hand steps). Do not publish the new text before the script is on
   `main`, or the commit SHA in the setup step will not exist.
4. **Then:** the owner runs the three cases once by hand against GitHub. Add the dated note to
   0001_copier_template_repo.md about `.gitignore`.
5. **Parallel, any time:** shellcheck can be tried locally while the script is written.
6. **Must not be bundled with:** the adoption mode (B3 in 0001_copier_template_repo.md), or any
   change to `template/`. They are different decisions with different failure modes.

## Implementation notes (2026-11-18)

Built, then committed by the owner as `75f4499` ("Shift to bash script") on `main`.

- **Built:** `scripts/new-project.sh` (executable, `shellcheck` 0.10.0 clean), tests N1 to N11 in
  `tests/test_generate.py`, the rewritten `README.md`, a `CHANGELOG.md` line, a renamed CI step,
  and a dated correction in 0001_copier_template_repo.md.
- **Tests:** `uv run --with copier==9.19.1 --with pytest pytest -q tests` gives 53 passed and 0
  skipped on this machine (22 earlier tests, 31 new).
- **Mutation checks, run in a scratch copy:**
  - The secret-lines append removed: N2 fails (two tests).
  - `uv init` run before Copier: N1 passed at first, because step 5 and step 8 repair the result.
    I added an assertion to N1 that nothing was appended for a new project. N1 now fails.
  - A `HEAD` fallback in `resolve_sha`: my first mutation was an equivalent mutant, because
    `git ls-remote … refs/heads/main` never returns `HEAD`. A stronger mutation (list all refs,
    accept `HEAD`) makes N7 fail.
  - The N9 control first crashed on a missing directory, which is the wrong failure. It now
    creates the directory and checks that the failing case is one with content.
- **Changed from the design above:**
  - The read-only target check runs before the network call (steps 3 and 4). The N5 `afile` case
    found it: with no SHA and no reachable repo, the script exited 1 where 2 is right.
  - `warn_other_readmes` also covers `README.rst` and `README`, and stays quiet when `README.md`
    exists.
  - `shellcheck` runs inside N10 through `uvx --from shellcheck-py==0.10.0.1`, not as a separate
    CI step. The CI step that runs the tests is renamed.
  - `scratch_template` in the tests dropped every directory named `journal`, including
    `template/journal`. It now drops only the repo's top-level `journal/`. The 22 earlier tests
    still pass.
- **README placeholder:** the setup URL keeps the `<commit-sha>` placeholder on purpose. Each
  reader picks the commit they have read. The README says how to find the latest one.
- **Run by hand against real GitHub (2026-11-18), with the working-tree script and the default
  `NPT_REPO_URL`:** the default SHA resolved to `33615e3b…` (the tip of `main`). A new project, a
  bare directory (empty README removed, three secret lines appended, `notes.txt` kept) and a
  directory with a `pyproject.toml` (`uv init` skipped, file unchanged) all worked. A well-formed
  SHA that does not exist exited 1 and left no directory.
- **After the commit (`75f4499`), checked by hand:**
  - `git ls-remote` shows `main` at `75f4499…`. The commit changes 7 files, including
    `scripts/new-project.sh`.
  - The README setup step, run as written with that SHA (`curl -fsSL …/75f4499…/scripts/new-project.sh`),
    downloaded 5193 bytes. The file is byte-identical to the working copy (same SHA-256).
  - The downloaded copy, run as `npt-copier` with the default URL and no SHA, resolved the latest
    `main` to `75f4499…`, created the project, and recorded `_commit: 75f4499`.
  - GitHub Actions run 44350060163 on that commit succeeded. `generate`: `52 passed, 1 skipped`
    (T10, as before). `speckit`: `1 passed, 52 deselected`, so T10 ran and passed.
- **Not tested:** Copier's per-file prompt when a terminal is present; macOS.
