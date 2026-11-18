"""Generation tests for the npt Copier template.

Each test generates a project into a temp directory and checks it. Tests that have a negative
control run the same check against a deliberately broken scratch copy of the template and
require the check to fail.

Run: uv run --with copier==9.19.1 --with pytest pytest -q tests
"""
import hashlib
import os
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
    skip_everywhere = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache")

    def ignore(dirpath, names):
        ignored = set(skip_everywhere(dirpath, names))
        if Path(dirpath) == REPO:
            ignored |= {"journal"} & set(names)  # the repo journal, not template/journal
        return ignored

    shutil.copytree(REPO, dst, ignore=ignore)
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


# --- scripts/new-project.sh (plan 0002, tests N1 to N11) -----------------------------------------

SCRIPT = REPO / "scripts" / "new-project.sh"
needs_uv = pytest.mark.skipif(
    shutil.which("uv") is None or shutil.which("uvx") is None, reason="uv is not on PATH"
)
PASS_THROUGH = ["--", "--defaults", "--data", "one_line_description=A demo"]
SECRET_LINES = [".env", ".env.*", ".claude/settings.local.json"]


def npt_repo(tmp_path: Path, branch="main", commits=2):
    """A local template repo for NPT_REPO_URL. Returns (path, [sha of each commit, oldest first])."""
    repo = scratch_template(tmp_path, "npt_repo")
    git(repo, "init", "-q", "-b", branch)
    shas = []
    for n in range(commits):
        if n:
            note = repo / "template/.claude/docs/known_gaps.md"
            note.write_text(note.read_text() + f"\nrevision {n}\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", f"commit {n}")
        shas.append(git(repo, "rev-parse", "HEAD").stdout.strip())
    return repo, shas


def script(args, cwd: Path, repo: Path, check=False):
    env = {**os.environ, "NPT_REPO_URL": str(repo)}
    result = subprocess.run(
        ["bash", str(SCRIPT), *args], cwd=cwd, env=env, capture_output=True, text=True
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"script exited {result.returncode}\n{result.stdout}\n{result.stderr}")
    return result


def answers(project: Path) -> dict:
    return yaml.safe_load((project / ".copier-answers.yml").read_text())


def uv_init(directory: Path):
    run(["uv", "init", "--no-workspace", "."], cwd=directory)


# --- N1: a new project ----------------------------------------------------------------------


@needs_uv
def test_n1_new_project(tmp_path):
    repo, shas = npt_repo(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    script(["myproj", shas[0], *PASS_THROUGH], work, repo, check=True)
    project = work / "myproj"
    assert_layout(project)
    assert (project / "pyproject.toml").is_file()
    assert (project / "README.md").read_text().startswith("# myproj")
    gitignore_text = (project / ".gitignore").read_text()
    assert all(line in gitignore_text.splitlines() for line in SECRET_LINES)
    # the template .gitignore was written, so the script appended nothing
    assert "added by npt-copier" not in gitignore_text
    assert "# Secrets and local Claude Code settings\n" in gitignore_text
    assert answers(project)["_commit"] == shas[0][:7]


@needs_uv
def test_n1_negative_control_old_order_loses_readme_and_gitignore(tmp_path):
    repo, _ = npt_repo(tmp_path)
    project = tmp_path / "old_order"
    project.mkdir()
    uv_init(project)  # the order the README used to document
    generate(repo, project)
    assert (project / "README.md").read_text() == ""
    assert ".env" not in (project / ".gitignore").read_text().splitlines()


# --- N2: a bare directory with content ------------------------------------------------------


@needs_uv
def test_n2_existing_directory_with_content(tmp_path):
    repo, shas = npt_repo(tmp_path)
    work = tmp_path / "work"
    project = work / "bare"
    project.mkdir(parents=True)
    (project / "notes.txt").write_text("my notes\n")
    (project / ".gitignore").write_text("mine.log\n")
    (project / "README.md").write_text("")
    script(["bare", shas[1], *PASS_THROUGH], work, repo, check=True)
    assert (project / "notes.txt").read_text() == "my notes\n"
    assert (project / "README.md").read_text().startswith("# bare")
    lines = (project / ".gitignore").read_text().splitlines()
    assert lines[0] == "mine.log"
    assert all(line in lines for line in SECRET_LINES)
    assert (project / "pyproject.toml").is_file()


@needs_uv
def test_n2_negative_control_readme_with_content_is_kept(tmp_path):
    repo, shas = npt_repo(tmp_path)
    work = tmp_path / "work"
    project = work / "bare"
    project.mkdir(parents=True)
    (project / "README.md").write_text("# mine\n\nreal content\n")
    script(["bare", shas[1], *PASS_THROUGH], work, repo, check=True)
    assert (project / "README.md").read_text() == "# mine\n\nreal content\n"


@needs_uv
def test_n2_gitignore_without_trailing_newline_is_appended_safely(tmp_path):
    repo, shas = npt_repo(tmp_path)
    work = tmp_path / "work"
    project = work / "bare"
    project.mkdir(parents=True)
    (project / ".gitignore").write_text("mine.log")  # no newline at the end
    script(["bare", shas[1], *PASS_THROUGH], work, repo, check=True)
    lines = (project / ".gitignore").read_text().splitlines()
    assert lines[0] == "mine.log"
    assert all(line in lines for line in SECRET_LINES)


# --- N3: another README file with content ---------------------------------------------------


@needs_uv
def test_n3_lowercase_readme_with_content_is_kept_and_warned(tmp_path):
    repo, shas = npt_repo(tmp_path)
    work = tmp_path / "work"
    project = work / "legacy"
    project.mkdir(parents=True)
    (project / "readme.md").write_text("# legacy\n")
    result = script(["legacy", shas[1], *PASS_THROUGH], work, repo, check=True)
    assert (project / "readme.md").read_text() == "# legacy\n"
    assert (project / "README.md").is_file()
    assert "readme.md exists and is kept" in result.stderr


# --- N4: the default is the latest commit on main --------------------------------------------


@needs_uv
def test_n4_default_sha_is_tip_of_main(tmp_path):
    repo, shas = npt_repo(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    result = script(["latest", *PASS_THROUGH], work, repo, check=True)
    assert answers(work / "latest")["_commit"] == shas[1][:7]
    assert shas[1] in result.stdout, "the full SHA must be printed"


@needs_uv
def test_n4_negative_control_explicit_older_sha_is_used(tmp_path):
    repo, shas = npt_repo(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    script(["older", shas[0], *PASS_THROUGH], work, repo, check=True)
    assert answers(work / "older")["_commit"] == shas[0][:7]


# --- N5: bad arguments change nothing -------------------------------------------------------


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["../x"],
        ["a b"],
        ["-x"],
        ["a" * 81],
        ["ok", "zzzzzzz"],
        ["ok", "abc"],
        ["ok", "ABCDEF1"],
        ["ok", "abcdef1", "stray"],
        ["afile"],
    ],
    ids=lambda a: " ".join(a)[:20] or "no-args",
)
def test_n5_bad_arguments_exit_2_and_create_nothing(tmp_path, args):
    work = tmp_path / "work"
    work.mkdir()
    (work / "afile").write_text("i am a file\n")
    before = sorted(p.name for p in tmp_path.rglob("*"))
    result = script(args, work, repo=tmp_path / "no_such_repo")
    assert result.returncode == 2, result.stderr
    assert sorted(p.name for p in tmp_path.rglob("*")) == before


# --- N6: an existing pyproject.toml ---------------------------------------------------------


@needs_uv
def test_n6_existing_pyproject_skips_uv_init(tmp_path):
    repo, shas = npt_repo(tmp_path)
    work = tmp_path / "work"
    project = work / "haspy"
    project.mkdir(parents=True)
    pyproject = '[project]\nname = "haspy"\nversion = "0"\n'
    (project / "pyproject.toml").write_text(pyproject)
    result = script(["haspy", shas[1], *PASS_THROUGH], work, repo, check=True)
    assert (project / "pyproject.toml").read_text() == pyproject
    assert "skipped uv init" in result.stdout


@needs_uv
def test_n6_negative_control_plain_uv_init_fails_on_existing_pyproject(tmp_path):
    project = tmp_path / "haspy"
    project.mkdir()
    (project / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0"\n')
    assert run(["uv", "init", "--no-workspace", "."], cwd=project, check=False).returncode != 0


# --- N7: no main branch ---------------------------------------------------------------------


def test_n7_missing_main_branch_stops_before_creating_anything(tmp_path):
    repo, _ = npt_repo(tmp_path, branch="trunk")
    work = tmp_path / "work"
    work.mkdir()
    result = script(["proj"], work, repo)
    assert result.returncode != 0
    assert "no refs/heads/main" in result.stderr
    assert list(work.iterdir()) == []


# --- N8: a well-formed SHA that does not exist ----------------------------------------------


@needs_uv
def test_n8_unknown_sha_removes_the_directory_it_created(tmp_path):
    repo, _ = npt_repo(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    result = script(["proj", "deadbeefdeadbeef", *PASS_THROUGH], work, repo)
    assert result.returncode != 0
    assert not (work / "proj").exists()


@needs_uv
def test_n8_negative_control_existing_directory_is_left_alone(tmp_path):
    repo, _ = npt_repo(tmp_path)
    work = tmp_path / "work"
    (work / "proj").mkdir(parents=True)
    (work / "proj" / "keep.txt").write_text("keep\n")
    result = script(["proj", "deadbeefdeadbeef", *PASS_THROUGH], work, repo)
    assert result.returncode != 0
    assert (work / "proj" / "keep.txt").read_text() == "keep\n"


# --- N9: the empty-README step, called directly ---------------------------------------------

EMPTY_README_CASES = {
    # name: (files {name: bytes or "dir" or "link"}, expected remaining names)
    "zero bytes": ({"README.md": b""}, set()),
    "whitespace only": ({"README.md": b"\n  \t\n"}, set()),
    "lowercase empty": ({"readme.md": b""}, set()),
    "mixed case empty": ({"Readme.md": b""}, set()),
    "empty lowercase beside content": (
        {"readme.md": b"", "README.md": b"keep\n"},
        {"README.md"},
    ),
    "content": ({"README.md": b"# mine\n"}, {"README.md"}),
    "one character": ({"README.md": b"x"}, {"README.md"}),
    "comment only": ({"README.md": b"<!-- todo -->\n"}, {"README.md"}),
    "binary": ({"README.md": b"\x00\x01\x02"}, {"README.md"}),
    "byte-order mark only": ({"README.md": b"\xef\xbb\xbf"}, {"README.md"}),
    "symlink": ({"README.md": "link"}, {"README.md"}),
    "directory": ({"README.md": "dir"}, {"README.md"}),
    "no file": ({}, set()),
}


def run_remove_empty_readmes(script_path: Path, directory: Path):
    return subprocess.run(
        ["bash", "-c", 'source "$1" && remove_empty_readmes', "bash", str(script_path)],
        cwd=directory,
        capture_output=True,
        text=True,
    )


def build_readme_case(directory: Path, files: dict):
    for name, content in files.items():
        if content == "dir":
            (directory / name).mkdir()
        elif content == "link":
            (directory.parent / "elsewhere_empty").write_bytes(b"")
            (directory / name).symlink_to(directory.parent / "elsewhere_empty")
        else:
            (directory / name).write_bytes(content)


def assert_empty_readme_cases(script_path: Path, tmp_path: Path):
    for label, (files, expected) in EMPTY_README_CASES.items():
        directory = tmp_path / label.replace(" ", "_")
        directory.mkdir()
        build_readme_case(directory, files)
        result = run_remove_empty_readmes(script_path, directory)
        assert result.returncode == 0, (label, result.stderr)
        assert {p.name for p in directory.iterdir()} == expected, label


def test_n9_empty_readme_cases(tmp_path):
    assert_empty_readme_cases(SCRIPT, tmp_path)


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read a mode 000 file")
def test_n9_unreadable_file_is_kept(tmp_path):
    (tmp_path / "README.md").write_bytes(b"")
    (tmp_path / "README.md").chmod(0)
    try:
        assert run_remove_empty_readmes(SCRIPT, tmp_path).returncode == 0
        assert (tmp_path / "README.md").exists()
    finally:
        (tmp_path / "README.md").chmod(0o644)


def test_n9_negative_control_broken_condition_loses_content(tmp_path):
    text = SCRIPT.read_text()
    condition = "! LC_ALL=C grep -q '[^[:space:]]' \"$f\""
    assert text.count(condition) == 1, "the control must find the condition it breaks"
    broken = tmp_path / "broken.sh"
    broken.write_text(text.replace(condition, "true"))
    cases = tmp_path / "cases"
    cases.mkdir()
    with pytest.raises(AssertionError) as failure:
        assert_empty_readme_cases(broken, cases)
    # it must fail on a file with content, not for some other reason
    assert any(
        label in str(failure.value)
        for label in ("content", "one character", "comment only", "binary", "byte-order mark only")
    ), failure.value


# --- N10: shellcheck and the grep gate ------------------------------------------------------

DANGEROUS = re.compile(r"\beval\b|\bcurl\b|\bwget\b|\bsh\s+-c\b")


def assert_no_dangerous_calls(text: str):
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert not DANGEROUS.search(code), DANGEROUS.search(code).group(0)


def test_n10_grep_gate_passes_on_the_script():
    assert_no_dangerous_calls(SCRIPT.read_text())


def test_n10_negative_control(tmp_path):
    with pytest.raises(AssertionError):
        assert_no_dangerous_calls(SCRIPT.read_text() + '\neval "$1"\n')


def test_n10_scrub_gate_covers_scripts():
    assert_scrubbed(REPO / "scripts")


@pytest.mark.skipif(shutil.which("uvx") is None, reason="uvx is not on PATH")
def test_n10_shellcheck_passes():
    result = run(
        ["uvx", "--from", "shellcheck-py==0.10.0.1", "shellcheck", SCRIPT], check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


# --- N11: the README names the real command and files ---------------------------------------


def test_n11_readme_names_the_script_and_the_command():
    readme = (REPO / "README.md").read_text()
    assert "scripts/new-project.sh" in readme
    assert "npt-copier" in readme
    assert "npt-new" not in readme
    assert SCRIPT.is_file() and os.access(SCRIPT, os.X_OK)
