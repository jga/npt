#!/usr/bin/env bash
# Apply the npt Copier template to a new directory, or to a bare directory that has
# some content. Install it as `npt-copier`. See README.md for the steps it runs.
set -euo pipefail

NPT_REPO_URL="${NPT_REPO_URL:-https://github.com/jga/npt.git}"
COPIER_VERSION="9.19.1"

usage() {
  cat <<'EOF'
Usage: npt-copier <project-name> [<commit-sha>] [-- <copier args>...]

  <project-name>  Directory to create or reuse, and the project_name answer.
                  1-80 characters: letters, digits, dot, underscore, hyphen.
  <commit-sha>    Template commit, 7-40 hex characters. Default: latest commit on main.
  -- ...          Everything after -- goes to `copier copy` unchanged.

Environment:
  NPT_REPO_URL    Template repository. Default: https://github.com/jga/npt.git

Examples:
  npt-copier my-project
  npt-copier my-project 33615e3
  npt-copier my-project -- --defaults --data one_line_description="A demo"
EOF
}

fail() {
  local code=$1
  shift
  printf 'npt-copier: %s\n' "$*" >&2
  exit "$code"
}

validate_name() {
  [[ $1 =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$ ]]
}

validate_sha() {
  [[ $1 =~ ^[0-9a-f]{7,40}$ ]]
}

# Print the full SHA of refs/heads/main. Never falls back to another ref.
resolve_sha() {
  local out sha
  out=$(GIT_TERMINAL_PROMPT=0 git ls-remote "$NPT_REPO_URL" refs/heads/main) ||
    fail 1 "cannot read $NPT_REPO_URL"
  sha=$(printf '%s\n' "$out" | awk '$2 == "refs/heads/main" { print $1; exit }')
  [[ $sha =~ ^[0-9a-f]{40}$ ]] || fail 1 "no refs/heads/main in $NPT_REPO_URL"
  printf '%s\n' "$sha"
}

# In the current directory only: delete a README file (any case) that is a regular
# file, not a symlink, readable, and has no non-whitespace character.
remove_empty_readmes() {
  local f
  for f in [Rr][Ee][Aa][Dd][Mm][Ee].md; do
    if [ -f "$f" ] && [ ! -L "$f" ] && [ -r "$f" ] && ! LC_ALL=C grep -q '[^[:space:]]' "$f"; then
      rm -- "$f"
      printf 'removed empty %s\n' "$f"
    fi
  done
}

# Copier writes README.md when it is missing. Say so if another README file stays.
warn_other_readmes() {
  local f
  [ -e README.md ] && return 0
  for f in [Rr][Ee][Aa][Dd][Mm][Ee] [Rr][Ee][Aa][Dd][Mm][Ee].*; do
    if [ -e "$f" ]; then
      printf 'warning: %s exists and is kept. Copier will add README.md beside it.\n' "$f" >&2
    fi
  done
}

# Append, never remove: make sure .gitignore keeps secrets and local settings out of git.
ensure_gitignore_lines() {
  local line first=1
  for line in '.env' '.env.*' '.claude/settings.local.json'; do
    if ! grep -qxF -- "$line" .gitignore 2>/dev/null; then
      if [ "$first" -eq 1 ]; then
        if [ -s .gitignore ] && [ -n "$(tail -c1 .gitignore)" ]; then
          printf '\n' >>.gitignore
        fi
        printf '# Secrets and local Claude Code settings (added by npt-copier)\n' >>.gitignore
        first=0
      fi
      printf '%s\n' "$line" >>.gitignore
      printf 'added to .gitignore: %s\n' "$line"
    fi
  done
}

run_copier() {
  uvx --from "copier==$COPIER_VERSION" copier copy \
    --data "project_name=$NAME" \
    ${EXTRA[@]+"${EXTRA[@]}"} \
    "$NPT_REPO_URL" . --vcs-ref "$SHA"
}

main() {
  case "${1:-}" in
    -h | --help)
      usage
      return 0
      ;;
    '')
      usage >&2
      return 2
      ;;
  esac

  NAME=$1
  shift
  SHA=""
  EXTRA=()
  if [[ $# -gt 0 && $1 != -- ]]; then
    SHA=$1
    shift
  fi
  if [[ $# -gt 0 ]]; then
    [[ $1 == -- ]] || fail 2 "unexpected argument: $1"
    shift
    EXTRA=("$@")
  fi

  validate_name "$NAME" || fail 2 "bad project name '$NAME' (see --help)"
  if [[ -n $SHA ]]; then
    validate_sha "$SHA" || fail 2 "bad commit SHA '$SHA' (7-40 lowercase hex characters)"
  fi
  command -v git >/dev/null 2>&1 || fail 1 "git is not on PATH"
  command -v uv >/dev/null 2>&1 || fail 1 "uv is not on PATH"
  command -v uvx >/dev/null 2>&1 || fail 1 "uvx is not on PATH"

  # Read-only checks first: a bad target must fail before any network call.
  if [[ -L $NAME ]]; then
    fail 2 "$NAME is a symlink"
  elif [[ -e $NAME && ! -d $NAME ]]; then
    fail 2 "$NAME exists and is not a directory"
  fi

  # Resolve the SHA before the file system is changed.
  if [[ -z $SHA ]]; then
    SHA=$(resolve_sha)
    printf 'using latest main: %s\n' "$SHA"
  fi

  local created=0 start_dir=$PWD
  if [[ -d $NAME ]]; then
    printf 'using existing directory: %s\n' "$NAME"
  else
    mkdir -- "$NAME"
    created=1
    printf 'created directory: %s\n' "$NAME"
  fi
  cd -- "$NAME"

  remove_empty_readmes
  warn_other_readmes

  if ! run_copier; then
    cd -- "$start_dir"
    if [[ $created -eq 1 ]]; then
      rmdir -- "$NAME" 2>/dev/null || true
    fi
    fail 1 "copier failed. Nothing was run after it."
  fi

  ensure_gitignore_lines

  if [[ -e pyproject.toml ]]; then
    printf 'pyproject.toml exists: skipped uv init\n'
  else
    uv init --no-workspace .
  fi

  printf '\ndone: %s\ntemplate commit: %s\n' "$PWD" "$SHA"
  if [[ ! -d .git ]]; then
    printf 'note: this is not a git repository. copier update needs one: run git init.\n'
  fi
}

# Run main only when the file is executed. Tests source the file and call the functions.
if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  main "$@"
fi
