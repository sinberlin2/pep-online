# Commit all agent + docs work to branch dev (never stages .env)
# Run from pep-online folder in Git Bash or PowerShell where git works:
#   .\scripts\git-commit-to-dev.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git not found on PATH. Install Git for Windows or use GitHub Desktop."
}

$branch = git rev-parse --abbrev-ref HEAD 2>$null
if ($LASTEXITCODE -ne 0) { Write-Error "Not a git repository: $root" }

# Create or switch to dev
git fetch origin 2>$null
if (git show-ref --verify --quiet refs/heads/dev) {
    git checkout dev
} else {
    git checkout -b dev
}

# Stage everything except secrets
git add -A
git reset HEAD .env 2>$null
if (Test-Path .env) {
    git checkout -- .env 2>$null
}

$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "Nothing to commit (already clean on dev?)."
    git status -sb
    exit 0
}

git commit -m @"
Add site design agents (OpenAI concept_run) on dev branch.

- Pass 1: whole-site concept with web search and Revized/drinkpep anchors
- experiments/references, proposals, DEVELOPMENT/DEPLOY docs
- requirements-agents.txt; .env gitignored
"@

Write-Host ""
Write-Host "Committed on branch dev. Push with:"
Write-Host "  git push -u origin dev"
git status -sb
