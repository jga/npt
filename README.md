# npt

New Project Template (NPT).

A [Copier](https://copier.readthedocs.io) template for the Claude Code project layer: a thin
`CLAUDE.md`, imported convention files under `.claude/`, a `journal/` directory, and a starter
`README.md`. A bash script, `npt-copier`, applies the template and runs `uv init` for you.

The template is a layer, not a project scaffold. It creates no `pyproject.toml` or
`package.json`. The script adds `pyproject.toml` with `uv init`. For a JS or TS project, use the
by-hand steps below with `npm create` in place of `uv init`.

## Set up the script

```bash
mkdir -p ~/.local/bin
curl -fsSL https://raw.githubusercontent.com/jga/npt/<commit-sha>/scripts/new-project.sh \
  -o ~/.local/bin/npt-copier
less ~/.local/bin/npt-copier       # read it before you run it
chmod +x ~/.local/bin/npt-copier
```

- Replace `<commit-sha>` with a commit of this repo. The URL names a commit, not `main`, so the
  file cannot change after you read it. To get the latest commit on `main`:
  `git ls-remote https://github.com/jga/npt.git refs/heads/main`.
- `~/.local/bin` must be on your `PATH`.
- The script needs `bash`, `git` and [`uv`](https://docs.astral.sh/uv/) (which provides `uvx`).
  It checks for them at the start.
- It is tested on Linux. macOS is untested. On Windows, use WSL.

## Use the script

```bash
npt-copier my-project                 # latest commit on main
npt-copier my-project 33615e3         # a chosen template commit
npt-copier my-project -- --defaults --data one_line_description="A demo"   # no prompts
```

| Argument | Meaning |
|---|---|
| `<project-name>` | Required. The directory to create or reuse, and the `project_name` answer. 1 to 80 characters: letters, digits, `.`, `_`, `-`. |
| `<commit-sha>` | Optional. 7 to 40 lowercase hex characters. Default: the latest commit on `main`. The script prints the full SHA it used. |
| `-- ...` | Optional. Everything after `--` goes to `copier copy` unchanged. |

Set `NPT_REPO_URL` to use a fork or a local clone as the template source.

The script has two use cases:

1. **A new project.** The directory does not exist. The script creates it, applies the template,
   and runs `uv init`.
2. **A bare or minimal directory.** The directory exists and holds some files, but has no
   `pyproject.toml`. The script keeps your files, applies the template, and runs `uv init`. If a
   `pyproject.toml` already exists, it skips `uv init`.

Copier asks the remaining questions: a one-line description, the language, and the source
directory. The script never passes `--overwrite`. If a template file would change a file you
already have, Copier asks you, or keeps your file when it has no terminal.

## What is in the script

`scripts/new-project.sh` runs these steps in order:

1. Check the arguments. A bad name, a bad SHA or a stray argument exits with code 2, and nothing
   is created. A target that is a file or a symlink exits with code 2 too.
2. Check that `git`, `uv` and `uvx` are on `PATH`.
3. If no SHA was given, run `git ls-remote` for `refs/heads/main` and print the full SHA. If
   `main` does not exist, stop. The script does not guess another branch.
4. Create the directory, or use the existing one.
5. Delete a README file that is empty (zero bytes, or only whitespace). Any case counts:
   `README.md`, `readme.md`, `Readme.md`. A file with any content is kept. This matters because
   Copier never overwrites an existing `README.md`, so an empty one would stay empty.
6. If a `readme.md` (or `README.rst`, or `README`) with content is kept, print a warning. Copier
   will add `README.md` beside it.
7. Run `uvx --from copier==9.19.1 copier copy` with the SHA. The script pins the Copier version
   that the tests run against.
8. Make sure `.gitignore` has the lines `.env`, `.env.*` and `.claude/settings.local.json`. Lines
   are only appended, never removed, and each one added is printed. A new project already has them
   from the template.
9. Run `uv init --no-workspace .` unless `pyproject.toml` exists. `--no-workspace` stops `uv`
   from adding the project to a parent directory's workspace.
10. Print the directory and the template commit. Record the commit in your notes.

If Copier fails and the script created the directory, the script removes it with `rmdir`, which
only removes an empty directory.

Copier runs before `uv init` on purpose. `uv init` writes its own empty `README.md` and its own
`.gitignore`, and Copier does not overwrite those. In that order the template `README.md` and
`.gitignore` would be skipped. `uv init` does not overwrite existing files, so the reverse order
keeps the template files.

## How `uvx copier` works

- `uvx` runs a Python tool in a throwaway environment. Nothing is installed globally.
- `copier copy <url> <dest> --vcs-ref <sha>` clones the repo into a temp directory, checks out the
  SHA, and reads `copier.yml`. The setting `_subdirectory: template` means only the `template/`
  directory is rendered. This script and the tests are not copied.
- Copier asks the questions in `copier.yml`. It renders files whose names end in `.jinja`, and
  copies every other file byte for byte.
- A file in `_skip_if_exists` is written only when it does not exist yet. That protects your
  `CLAUDE.md`, `README.md` and `.gitignore`.
- Copier writes `.copier-answers.yml` with your answers and the template commit (`_commit`, in
  short form). Commit that file.
- Without `--vcs-ref`, Copier uses the latest git tag, or `HEAD` when the repo has no tags. The
  script always passes a SHA.

## The same steps by hand

```bash
mkdir my-project && cd my-project
uvx --from copier==9.19.1 copier copy https://github.com/jga/npt.git . --vcs-ref <commit-sha>
uv init --no-workspace .          # or: npm create ...
```

Run Copier first. For an existing directory, also delete any empty `README.md` first, because
Copier will not fill it in.

## Update a project

```bash
cd my-project
uvx --from copier==9.19.1 copier update --vcs-ref <commit-sha>
```

`copier update` reads `.copier-answers.yml`, and does a three-way merge between the old template,
the new template and your files. It needs a clean git working tree, and a git repository. Only
template-owned files change: `.claude/conventions.md` and `.claude/bqrs.md`. Everything else is
yours after the first copy.

## Threat model

- The template (`template/`) has no `_tasks`, no `_migrations` and no Jinja extensions, so it
  needs no `--trust`. A test fails if one is added.
- The template ships no hook, no script and no `settings.json`. The bootstrap script is outside
  `template/`: Copier never copies or runs it.
- The script is code that you run. Download it by commit SHA and read it first. It has no `eval`,
  no `curl` and no `sh -c`. It checks every argument before it uses it. Its only network use is
  `git ls-remote` and `uvx` with a pinned Copier version.
- The default (no SHA) takes whatever is on `main` at that moment. The template text is
  instructions to Claude, so review a commit before you rely on it. The script prints the SHA it
  used. Pass that SHA next time to repeat the result.
- Every answer that reaches a file has a `validator:` regex, and no question asks for a secret.
- Pin by commit SHA, not by tag. A tag can move.
- The next steps are printed, not run.

## Develop

```bash
uv run --with copier==9.19.1 --with pytest pytest -q tests
```

`tests/test_generate.py` generates projects into temp directories, and runs the script against a
local copy of the template. It also runs `shellcheck` through `uvx`. The SpecKit test (T10) is
skipped when the `specify` CLI is not on `PATH`.
