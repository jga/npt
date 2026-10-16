"""Generation tests for the npt Copier template.

Each test generates a project into a temp directory and checks it. Tests that have a negative
control run the same check against a deliberately broken scratch copy of the template and
require the check to fail.

Run: uv run --with copier==9.19.1 --with pytest pytest -q tests
"""
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

ANSWERS = {
    "project_name": "Demo Project",
    "one_line_description": "A demo project for the template tests.",
    "language": "python",
    "source_dir": "src",
}

REQUIRED = [
    "CLAUDE.md",
    "README.md",
    ".gitignore",
    ".copier-answers.yml",
    ".claude/conventions.md",
    ".claude/bqrs.md",
    ".claude/architecture_map.md",
    ".claude/docs/environment.md",
    ".claude/docs/known_gaps.md",
    "journal/CHANGELOG.md",
    "journal/misc/.gitkeep",
]
FORBIDDEN = [".claude/hooks", ".claude/settings.json"]


# --- helpers ---------------------------------------------------------------------------------


def run(cmd, cwd=None, check=True):
    result = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"{' '.join(str(c) for c in cmd)} exited {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def copier(*args, check=True):
    return run([sys.executable, "-m", "copier", *args], check=check)


def data_args(**overrides):
    answers = {**ANSWERS, **overrides}
    out = []
    for key, value in answers.items():
        out += ["--data", f"{key}={value}"]
    return out


def generate(template: Path, dst: Path, vcs_ref=None, **overrides):
    dst.mkdir(parents=True, exist_ok=True)
    args = ["copy", "--defaults", "--overwrite", "--quiet", *data_args(**overrides)]
    if vcs_ref:
        args += ["--vcs-ref", vcs_ref]
    copier(*args, template, dst)
    return dst


def scratch_template(tmp_path: Path, name="tpl") -> Path:
    """A copy of the template repo (working files only) that a test may break."""
    dst = tmp_path / name
    shutil.copytree(
        REPO, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "journal")
    )
    return dst


def git(cwd: Path, *args):
    return run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=cwd)


def tree_checksums(root: Path) -> dict:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


# --- checks (each is reused by its negative control) -----------------------------------------


def assert_layout(project: Path):
    for rel in REQUIRED:
        assert (project / rel).exists(), f"missing {rel}"
    for rel in FORBIDDEN:
        assert not (project / rel).exists(), f"must not exist: {rel}"


SCRUB = [
    r"/home/",
    r"@gmail",
    r"perry",
    r"terrastep",
    r"AKIA[0-9A-Z]{8,}",
    r"BEGIN [A-Z ]*PRIVATE KEY",
    r"s3://",
    r"\.s3\.amazonaws\.com",
]


def assert_scrubbed(template_dir: Path):
    hits = []
    for p in template_dir.rglob("*"):
        if not p.is_file():
            continue
        text = p.read_text(errors="replace")
        for pat in SCRUB:
            if re.search(pat, text, re.IGNORECASE):
                hits.append(f"{p.relative_to(template_dir)}: {pat}")
    assert not hits, hits


def assert_no_jinja_leftovers(project: Path):
    hits = [
        str(p.relative_to(project))
        for p in project.rglob("*")
        if p.is_file()
        and ".git" not in p.relative_to(project).parts
        and re.search(r"\{\{|\{%", p.read_text(errors="replace"))
    ]
    assert not hits, hits


def assert_bqrs_linked_not_imported(project: Path):
    claude = (project / "CLAUDE.md").read_text()
    assert ".claude/bqrs.md" in claude, "CLAUDE.md does not link bqrs.md"
    assert not re.search(r"^@\.claude/bqrs\.md", claude, re.MULTILINE), "bqrs.md is imported"
    assert "Blockers" not in (project / ".claude/conventions.md").read_text()


def assert_paths_resolve(project: Path):
    claude = (project / "CLAUDE.md").read_text()
    paths = re.findall(r"^@(\S+)", claude, re.MULTILINE)
    section = claude.split("## How this file is organized", 1)[1].split("\n## ", 1)[0]
    for token in re.findall(r"`([^`\s]+)`", section):
        if "/" in token or token.endswith(".md"):
            paths.append(token)
    assert paths, "no paths found: the check proves nothing"
    missing = [p for p in paths if not (project / p).exists()]
    assert not missing, missing


# --- T1 ------------------------------------------------------------------------------------


def test_t1_layout(tmp_path):
    assert_layout(generate(REPO, tmp_path / "p"))


def test_t1_negative_control(tmp_path):
    tpl = scratch_template(tmp_path)
    (tpl / "template/.claude/settings.json").write_text("{}\n")
    project = generate(tpl, tmp_path / "p")
    with pytest.raises(AssertionError):
        assert_layout(project)


@pytest.mark.parametrize("language", ["python", "typescript", "python+typescript", "other"])
def test_t1_every_language_generates(tmp_path, language):
    project = generate(REPO, tmp_path / "p", language=language)
    assert_layout(project)
    commands = (project / "CLAUDE.md").read_text().split("## Commands", 1)[1]
    assert "Run tests" in commands
    assert ("(Python)" in commands) == ("python" in language)
    assert ("(TypeScript)" in commands) == ("typescript" in language)


# --- T2: update changes template-owned files only ----------------------------------------


def _git_template(tmp_path: Path) -> Path:
    tpl = scratch_template(tmp_path, "gittpl")
    git(tpl, "init", "-q", "-b", "main")
    git(tpl, "add", "-A")
    git(tpl, "commit", "-q", "-m", "v0.1.0")
    git(tpl, "tag", "v0.1.0")
    return tpl


def _generated_repo(tpl: Path, dst: Path) -> Path:
    generate(tpl, dst, vcs_ref="v0.1.0")
    git(dst, "init", "-q", "-b", "main")
    claude = dst / "CLAUDE.md"
    claude.write_text(claude.read_text() + "\nProject-specific rule: use tabs.\n")
    git(dst, "add", "-A")
    git(dst, "commit", "-q", "-m", "project")
    return dst


def _update(project: Path, ref: str):
    run(
        [sys.executable, "-m", "copier", "update", "--defaults", "--quiet",
         "--vcs-ref", ref],
        cwd=project,
    )


def test_t2_update_changes_conventions_and_keeps_claude_md(tmp_path):
    tpl = _git_template(tmp_path)
    project = _generated_repo(tpl, tmp_path / "p")
    before = (project / "CLAUDE.md").read_bytes()

    conv = tpl / "template/.claude/conventions.md"
    conv.write_text(conv.read_text() + "\n## A new rule (standing preference)\n\nIt is new.\n")
    git(tpl, "commit", "-q", "-am", "v0.1.1")
    git(tpl, "tag", "v0.1.1")

    _update(project, "v0.1.1")
    assert "A new rule" in (project / ".claude/conventions.md").read_text()
    assert (project / "CLAUDE.md").read_bytes() == before


def test_t2_negative_control_skip_if_exists_file_changed_in_template(tmp_path):
    tpl = _git_template(tmp_path)
    project = _generated_repo(tpl, tmp_path / "p")
    before = (project / "CLAUDE.md").read_bytes()

    claude_tpl = tpl / "template/CLAUDE.md.jinja"
    claude_tpl.write_text(claude_tpl.read_text() + "\nTemplate-side change that must not land.\n")
    git(tpl, "commit", "-q", "-am", "v0.1.1")
    git(tpl, "tag", "v0.1.1")

    _update(project, "v0.1.1")
    assert (project / "CLAUDE.md").read_bytes() == before


# --- T3: an existing README.md and CLAUDE.md are not overwritten --------------------------
# ADOPT.md is part of the adoption mode, which ships in v0.2 (see B3 in the plan).


def test_t3_existing_files_are_kept(tmp_path):
    project = tmp_path / "legacy"
    shutil.copytree(FIXTURES / "legacy_project", project)
    before = tree_checksums(project)
    generate(REPO, project)
    after = tree_checksums(project)
    for rel in ("README.md", "CLAUDE.md"):
        assert after[rel] == before[rel], f"{rel} was overwritten"
    assert ".claude/conventions.md" in after


# --- T4 / T7: no trust needed -------------------------------------------------------------


def test_t4_copy_without_trust_succeeds(tmp_path):
    generate(REPO, tmp_path / "p")  # copier refuses an unsafe template without --trust


def test_t4_copier_yml_has_no_unsafe_keys():
    config = yaml.safe_load((REPO / "copier.yml").read_text())
    for key in ("_tasks", "_migrations", "_jinja_extensions"):
        assert key not in config, key


@pytest.mark.parametrize(
    "extra", ["_tasks:\n  - echo hello\n", "_jinja_extensions:\n  - jinja2_time.TimeExtension\n"]
)
def test_t7_unsafe_feature_is_refused_without_trust(tmp_path, extra):
    tpl = scratch_template(tmp_path)
    with (tpl / "copier.yml").open("a") as f:
        f.write("\n" + extra)
    dst = tmp_path / "p"
    dst.mkdir()
    result = copier(
        "copy", "--defaults", "--quiet", *data_args(), tpl, dst, check=False
    )
    assert result.returncode != 0, "copier ran an unsafe template without --trust"
    assert not (dst / "CLAUDE.md").exists()


# --- T5 ---------------------------------------------------------------------------------


def test_t5_scrub_gate_passes_on_the_template():
    assert_scrubbed(REPO / "template")


def test_t5_negative_control(tmp_path):
    tpl = scratch_template(tmp_path)
    (tpl / "template/.claude/docs/environment.md").write_text("see /home/x/notes\n")
    with pytest.raises(AssertionError):
        assert_scrubbed(tpl / "template")


# --- T6 ---------------------------------------------------------------------------------


def test_t6_no_jinja_in_generated_files(tmp_path):
    assert_no_jinja_leftovers(generate(REPO, tmp_path / "p"))


def test_t6_negative_control(tmp_path):
    tpl = scratch_template(tmp_path)
    arch = tpl / "template/.claude/architecture_map.md.jinja"
    arch.write_text(arch.read_text() + "{{ '{{' }} planted\n")
    project = generate(tpl, tmp_path / "p")
    with pytest.raises(AssertionError):
        assert_no_jinja_leftovers(project)


# --- T8 ---------------------------------------------------------------------------------


def test_t8_bqrs_is_linked_not_imported(tmp_path):
    assert_bqrs_linked_not_imported(generate(REPO, tmp_path / "p"))


def test_t8_negative_control(tmp_path):
    project = generate(REPO, tmp_path / "p")
    claude = project / "CLAUDE.md"
    claude.write_text(claude.read_text() + "@.claude/bqrs.md\n")
    with pytest.raises(AssertionError):
        assert_bqrs_linked_not_imported(project)


# --- T9 ---------------------------------------------------------------------------------


def test_t9_claude_md_paths_resolve(tmp_path):
    assert_paths_resolve(generate(REPO, tmp_path / "p"))


def test_t9_negative_control(tmp_path):
    tpl = scratch_template(tmp_path)
    (tpl / "template/.claude/bqrs.md").unlink()
    project = generate(tpl, tmp_path / "p")
    with pytest.raises(AssertionError):
        assert_paths_resolve(project)


# --- T10: SpecKit init does not overwrite template files ------------------------------------


@pytest.mark.skipif(shutil.which("specify") is None, reason="specify CLI is not on PATH")
def test_t10_speckit_init_does_not_overwrite_template_files(tmp_path):
    project = generate(REPO, tmp_path / "p")
    git(project, "init", "-q", "-b", "main")
    before = tree_checksums(project)

    run(
        ["specify", "init", "--here", "--force", "--non-interactive", "--ignore-agent-tools",
         "--integration", "claude"],
        cwd=project,
    )

    after = tree_checksums(project)
    # control: SpecKit must have written its own files, or the comparison proves nothing
    assert (project / ".specify").is_dir(), "specify init did not run"
    changed = sorted(p for p in before if after.get(p) != before[p])
    assert not changed, f"specify init changed template files: {changed}"
