#!/bin/bash
# Bootstrap a new BBE-DBE service from templates/service-skeleton.
#
# Usage:
#   bash new-service.sh <name> <db-schema> <default-port> [<one-line description>]
#
# Example:
#   bash new-service.sh netcup-api netcup 5360 "Netcup provider adapter"
#
# Result:
#   ~/projects/<name>/                                  (scaffold ready)
#     - placeholders substituted (__SERVICE_NAME__, __DB_SCHEMA__,
#       __DEFAULT_PORT__, __SERVICE_DESC__)
#     - git initialised, first commit made
#     - operator next-steps printed
#
# The script does NOT:
#   - create the GitHub repo (operator runs `gh repo create` after review)
#   - install dependencies (operator decides pnpm/npm/yarn at fork time)
#   - touch infra-postgres (the schema must be pre-provisioned by the
#     operator — see operator-todo at the end)
set -euo pipefail

if [[ $# -lt 3 ]]; then
  cat >&2 <<EOF
usage: $0 <name> <db-schema> <default-port> [<description>]
  name           kebab-case, e.g. netcup-api
  db-schema      snake_case, e.g. netcup
  default-port   integer, e.g. 5360
  description    optional one-liner
EOF
  exit 2
fi

NAME="$1"
SCHEMA="$2"
PORT="$3"
DESC="${4:-${NAME} (description pending)}"

# --- validation ---------------------------------------------------------
[[ "${NAME}"   =~ ^[a-z][a-z0-9-]+$ ]] || { echo "[new-service] name must be kebab-case ([a-z][a-z0-9-]+)" >&2; exit 2; }
[[ "${SCHEMA}" =~ ^[a-z][a-z0-9_]+$ ]] || { echo "[new-service] db-schema must be snake_case ([a-z][a-z0-9_]+)" >&2; exit 2; }
[[ "${PORT}"   =~ ^[0-9]+$ ]] || { echo "[new-service] default-port must be a positive integer" >&2; exit 2; }
[[ "${PORT}" -ge 1024 && "${PORT}" -le 65535 ]] || { echo "[new-service] port must be 1024..65535" >&2; exit 2; }

# --- locations ----------------------------------------------------------
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SKEL="${HERE}/templates/service-skeleton"
TARGET="${HOME}/projects/${NAME}"

if [[ ! -d "${SKEL}" ]]; then
  echo "[new-service] skeleton missing at ${SKEL}" >&2; exit 1
fi
if [[ -e "${TARGET}" ]]; then
  echo "[new-service] target already exists: ${TARGET}" >&2; exit 1
fi

echo "[new-service] copying skeleton → ${TARGET}"
mkdir -p "${TARGET}"
# rsync preserves perms (incl. +x on scripts/) and is more predictable than cp -r
rsync -a --exclude='.git' --exclude='node_modules' --exclude='dist' \
  "${SKEL}/" "${TARGET}/"

# --- placeholder substitution ------------------------------------------
echo "[new-service] substituting placeholders"
# We touch every non-binary file. Limit scope to the files we know exist.
escaped_desc="${DESC//\//\\/}"   # description may contain slashes
find "${TARGET}" -type f \
  \( -name '*.md' -o -name '*.json' -o -name '*.ts' -o -name '*.cjs' \
     -o -name '*.sql' -o -name '*.sh' -o -name '*.yml' -o -name '*.yaml' \
     -o -name '*.toml' -o -name '.env.example' -o -name '.gitignore' \) \
  -print0 \
| while IFS= read -r -d '' f; do
    sed -i \
      -e "s|__SERVICE_NAME__|${NAME}|g" \
      -e "s|__DB_SCHEMA__|${SCHEMA}|g" \
      -e "s|__DEFAULT_PORT__|${PORT}|g" \
      -e "s|__SERVICE_DESC__|${escaped_desc}|g" \
      "$f"
  done

# --- git init -----------------------------------------------------------
echo "[new-service] git init"
( cd "${TARGET}" \
  && git init -b main >/dev/null \
  && git add -A \
  && git commit -m "feat: initialise ${NAME} from api-standards/templates/service-skeleton" >/dev/null )

# --- operator next-steps ------------------------------------------------
cat <<EOF

[new-service] ✓ done at ${TARGET}

Operator-TODO (in this order):

  1) Provision the ${SCHEMA} schema + service-user in infra-postgres:
       (this requires editing ~/projects/infra-postgres/init/01-init.sh
        OR running an ad-hoc psql, depending on whether infra-postgres
        is already initialised. See infra-postgres/README.md.)

  2) cd ${TARGET}
     cp .env.example .env       # fill PGPASSWORD with the new service-user's pwd
     pnpm install
     pnpm migrate
     pnpm build
     pnpm test                  # vitest will pass with the skeleton's smoke test

  3) gh repo create BBE-DBE/${NAME} --private --source=. --push --description "${DESC}"

  4) PM2:  pm2 start ecosystem.config.cjs && pm2 save

EOF
