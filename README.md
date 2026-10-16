# npt

New Project Template (NPT).

A [Copier](https://copier.readthedocs.io) template for the Claude Code project layer: a thin
`CLAUDE.md`, imported convention files under `.claude/`, a `journal/` directory, and a starter
`README.md`.

It is a layer, not a project scaffold. It creates no `pyproject.toml` or `package.json`. Run
`uv init` (or `npm create`) first, then `copier copy`.

## Use

```bash
uv init my-project && cd my-project
uvx copier copy https://github.com/jga/npt.git . --vcs-ref <commit-sha>

# later, pull template changes
uvx copier update --vcs-ref <commit-sha>
```

`copier update` needs a clean git working tree. Only template-owned files change:
`.claude/conventions.md` and `.claude/bqrs.md`. Everything else is yours after the first copy.

## Threat model

- The template has no `_tasks`, no `_migrations` and no Jinja extensions, so it needs no
  `--trust`. A test fails if one is added.
- It ships no hook, no script and no `settings.json`. It runs nothing on your machine.
- Every answer that reaches a file has a `validator:` regex, and no question asks for a secret.
- Pin by commit SHA, not by tag. A tag can move.
- The next steps are printed, not run.

## Develop

```bash
uv run --with copier==9.19.1 --with pytest pytest -q tests
```

`tests/test_generate.py` generates projects into temp directories. The SpecKit test (T10) is
skipped when the `specify` CLI is not on `PATH`.
