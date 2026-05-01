#!/bin/bash
# SHA-256-drift-checked migration runner. Headers parsed:
#   -- Author: <name>
#   -- Date:   YYYY-MM-DD
#   -- Commit: <ref>
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

if [[ ! -f .env ]]; then echo "[migrate] .env missing" >&2; exit 1; fi
# shellcheck disable=SC1091
set -a; . ./.env; set +a

CONTAINER="${POSTGRES_CONTAINER:-infra-postgres}"
PSQL=(docker exec -i -e "PGPASSWORD=${PGPASSWORD}" "${CONTAINER}"
  psql -h 127.0.0.1 -p 5432 -U "${PGUSER}" -d "${PGDATABASE}"
  -v ON_ERROR_STOP=1 --no-psqlrc -tA)

# Bootstrap (idempotent): the schema must already exist (operator
# provisions it in infra-postgres). 001_init.sql creates schema_migrations.
"${PSQL[@]}" <<SQL >/dev/null
CREATE TABLE IF NOT EXISTS ${PG_SCHEMA}.schema_migrations (
  filename TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

parse_header_field() {
  local file="$1" field="$2"
  awk -v f="${field}" '
    /^[[:space:]]*--/ {
      line=$0; sub(/^[[:space:]]*-- /, "", line); sub(/^[[:space:]]*--/, "", line)
      if (match(line, "^"f"[[:space:]]*:[[:space:]]*")) {
        v=substr(line, RSTART+RLENGTH); sub(/[[:space:]]+$/, "", v)
        print v; exit
      }
      next
    }
    /[^[:space:]]/ { exit }
  ' "${file}"
}

shopt -s nullglob
applied=0
skipped=0
for f in "${ROOT}"/db/migrations/*.sql; do
  base="$(basename "$f")"
  sum="$(sha256sum "$f" | awk '{print $1}')"
  author="$(parse_header_field "$f" 'Author')"
  date_field="$(parse_header_field "$f" 'Date')"
  commit_field="$(parse_header_field "$f" 'Commit')"

  has_csum_col="$("${PSQL[@]}" -c "SELECT 1 FROM information_schema.columns WHERE table_schema='${PG_SCHEMA}' AND table_name='schema_migrations' AND column_name='checksum'")"
  has_author_col="$("${PSQL[@]}" -c "SELECT 1 FROM information_schema.columns WHERE table_schema='${PG_SCHEMA}' AND table_name='schema_migrations' AND column_name='author'")"
  recorded="$("${PSQL[@]}" -c "SELECT 1 FROM ${PG_SCHEMA}.schema_migrations WHERE filename='${base}'")"

  if [[ "${recorded}" == "1" ]]; then
    if [[ "${has_csum_col}" == "1" ]]; then
      stored="$("${PSQL[@]}" -c "SELECT COALESCE(checksum,'') FROM ${PG_SCHEMA}.schema_migrations WHERE filename='${base}'")"
      if [[ -n "${stored}" && "${stored}" != "${sum}" ]]; then
        echo "[migrate] FATAL: ${base} drifted — stored=${stored} file=${sum}" >&2; exit 2
      fi
      [[ -z "${stored}" ]] && \
        "${PSQL[@]}" -c "UPDATE ${PG_SCHEMA}.schema_migrations SET checksum='${sum}' WHERE filename='${base}'" >/dev/null
    fi
    if [[ "${has_author_col}" == "1" && -n "${author}" ]]; then
      authored_sql="now()"
      [[ -n "${date_field}" ]] && authored_sql="'${date_field//\'/\'\'}'::timestamptz"
      "${PSQL[@]}" -c "
        UPDATE ${PG_SCHEMA}.schema_migrations
           SET author      = COALESCE(author, '${author//\'/\'\'}'),
               authored_at = COALESCE(authored_at, ${authored_sql}),
               git_commit  = COALESCE(git_commit, '${commit_field//\'/\'\'}')
         WHERE filename = '${base}'" >/dev/null
    fi
    echo "[migrate] skip   ${base}"
    skipped=$((skipped + 1))
    continue
  fi

  echo "[migrate] apply  ${base}  sha256=${sum:0:12}…  author=${author:-?}"
  "${PSQL[@]}" < "${f}" >/dev/null

  has_csum_col="$("${PSQL[@]}" -c "SELECT 1 FROM information_schema.columns WHERE table_schema='${PG_SCHEMA}' AND table_name='schema_migrations' AND column_name='checksum'")"
  has_author_col="$("${PSQL[@]}" -c "SELECT 1 FROM information_schema.columns WHERE table_schema='${PG_SCHEMA}' AND table_name='schema_migrations' AND column_name='author'")"

  cols=("filename"); vals=("'${base}'")
  if [[ "${has_csum_col}" == "1" ]]; then cols+=("checksum");   vals+=("'${sum}'"); fi
  if [[ "${has_author_col}" == "1" ]]; then
    [[ -n "${author}" ]] && { cols+=("author"); vals+=("'${author//\'/\'\'}'"); }
    [[ -n "${date_field}"   ]] && { cols+=("authored_at"); vals+=("'${date_field}'::timestamptz"); }
    [[ -n "${commit_field}" ]] && { cols+=("git_commit"); vals+=("'${commit_field//\'/\'\'}'"); }
  fi
  cols_csv="$(IFS=,; echo "${cols[*]}")"
  vals_csv="$(IFS=,; echo "${vals[*]}")"
  "${PSQL[@]}" -c "INSERT INTO ${PG_SCHEMA}.schema_migrations(${cols_csv}) VALUES (${vals_csv})" >/dev/null
  applied=$((applied + 1))
done

echo "[migrate] done — applied=${applied}, skipped=${skipped}"
