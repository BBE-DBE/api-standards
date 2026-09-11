#!/usr/bin/env bash
# fetch_repos.sh — refresh registry/repos.snapshot.tsv from the GitHub API.
#
# The register is only as honest as its snapshot. Re-run this before every
# review cycle, then run scripts/build_registry.py.
#
#   GITHUB_TOKEN=ghp_... ./scripts/fetch_repos.sh BBE-DBE SSR-SFS
#
# Requires: curl, jq. Needs a token with `repo` scope (private repos).
set -euo pipefail

: "${GITHUB_TOKEN:?set GITHUB_TOKEN (scope: repo)}"
ORGS=("${@:-BBE-DBE}")
OUT="$(cd "$(dirname "$0")/.." && pwd)/registry/repos.snapshot.tsv"
TMP="$(mktemp)"

printf 'full_name\tcreated_at\tpushed_at\tlanguage\tprivate\tdefault_branch\topen_issues\tdescription\n' > "$TMP"

for org in "${ORGS[@]}"; do
  page=1
  while :; do
    body="$(curl -fsSL \
      -H "Authorization: Bearer ${GITHUB_TOKEN}" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/orgs/${org}/repos?per_page=100&page=${page}&type=all&sort=pushed")"
    count="$(jq 'length' <<<"$body")"
    [ "$count" -eq 0 ] && break
    # Tabs and newlines inside descriptions would corrupt the TSV — strip them.
    jq -r '.[] | [
        .full_name, .created_at, .pushed_at, (.language // ""),
        (.private|tostring), .default_branch, (.open_issues_count|tostring),
        ((.description // "") | gsub("[\t\n\r]"; " "))
      ] | @tsv' <<<"$body" >> "$TMP"
    page=$((page + 1))
  done
done

mv "$TMP" "$OUT"
echo "$(( $(wc -l < "$OUT") - 1 )) repos -> $OUT"
echo "next: python3 scripts/build_registry.py"
