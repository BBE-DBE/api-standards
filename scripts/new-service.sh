#!/bin/bash
# Bootstrap a new BBE-DBE service from templates/service-skeleton.
#
# Two invocation forms — pick whichever reads better in your context.
# Both validate identically and produce identical results.
#
# (1) Positional (legacy, kept for backward-compat):
#
#     bash new-service.sh <name> <db-schema> <default-port> [<description>]
#
#     Example:
#       bash new-service.sh netcup-api netcup 5360 "Netcup adapter"
#
# (2) Flag form (preferred for reproducible / scripted bootstraps):
#
#     bash new-service.sh <name> \
#       --schema=<snake_case> \
#       --port=<1024..65535> \
#       [--prefix=<2-4 lowercase letters>] \
#       [--token-prefix=<alias of --prefix>] \
#       [--with-auth] \
#       [--desc="<one-liner>"]
#
#     Example:
#       bash new-service.sh port-registry \
#         --schema=port_registry --port=5300 \
#         --prefix=prr --with-auth \
#         --desc="Single Source of Truth for server ports"
#
# Flags:
#   --schema       (required if not given positionally)  snake_case
#   --port         (required if not given positionally)  1024..65535
#   --prefix       (optional)  2-4 lowercase letters; reserved per
#                  service in _optional/auth/README.md
#   --token-prefix (optional)  alias of --prefix
#   --with-auth    (optional)  copy _optional/auth/migration.sql into
#                  db/migrations/002_auth.sql with substitution
#   --desc         (optional)  one-line service description
#
# Result:
#   ~/projects/<name>/                                  (scaffold ready)
#     - placeholders substituted (__SERVICE_NAME__, __DB_SCHEMA__,
#       __DEFAULT_PORT__, __SERVICE_DESC__, __TOKEN_PREFIX__)
#     - git initialised, first commit made
#     - operator next-steps printed
#
# The script does NOT:
#   - create the GitHub repo (operator runs `gh repo create` after review)
#   - install dependencies (operator decides pnpm/npm/yarn at fork time)
#   - touch infra-postgres (the schema must be pre-provisioned by the
#     operator — see operator-todo at the end)
set -euo pipefail

# --- usage --------------------------------------------------------------
usage() {
  cat >&2 <<EOF
usage:
  $0 <name> <db-schema> <default-port> [<description>]
  $0 <name> --schema=<schema> --port=<port> [--prefix=<2-4>] [--with-auth] [--desc="..."]

Example (positional):
  $0 netcup-api netcup 5360 "Netcup adapter"

Example (flags):
  $0 port-registry --schema=port_registry --port=5300 --prefix=prr --with-auth
EOF
  exit 2
}

# --- parse --------------------------------------------------------------
NAME=""
SCHEMA=""
PORT=""
DESC=""
TOKEN_PREFIX=""
WITH_AUTH="0"

POSITIONAL=()
for arg in "$@"; do
  case "${arg}" in
    --schema=*)        SCHEMA="${arg#*=}" ;;
    --port=*)          PORT="${arg#*=}" ;;
    --prefix=*)        TOKEN_PREFIX="${arg#*=}" ;;
    --token-prefix=*)  TOKEN_PREFIX="${arg#*=}" ;;
    --desc=*)          DESC="${arg#*=}" ;;
    --with-auth)       WITH_AUTH="1" ;;
    --help|-h)         usage ;;
    --*)               echo "[new-service] unknown flag: ${arg}" >&2; usage ;;
    *)                 POSITIONAL+=("${arg}") ;;
  esac
done

# Positional fallback: name [schema port [desc]]
if [[ -z "${NAME}" && ${#POSITIONAL[@]} -ge 1 ]]; then
  NAME="${POSITIONAL[0]}"
fi
if [[ -z "${SCHEMA}" && ${#POSITIONAL[@]} -ge 2 ]]; then
  SCHEMA="${POSITIONAL[1]}"
fi
if [[ -z "${PORT}"   && ${#POSITIONAL[@]} -ge 3 ]]; then
  PORT="${POSITIONAL[2]}"
fi
if [[ -z "${DESC}"   && ${#POSITIONAL[@]} -ge 4 ]]; then
  DESC="${POSITIONAL[3]}"
fi

# --- validation ---------------------------------------------------------
[[ -n "${NAME}"   ]] || { echo "[new-service] missing <name>" >&2;        usage; }
[[ -n "${SCHEMA}" ]] || { echo "[new-service] missing --schema/<schema>" >&2; usage; }
[[ -n "${PORT}"   ]] || { echo "[new-service] missing --port/<port>"     >&2; usage; }

[[ "${NAME}"   =~ ^[a-z][a-z0-9-]+$ ]] || { echo "[new-service] name must be kebab-case ([a-z][a-z0-9-]+)" >&2; exit 2; }
[[ "${SCHEMA}" =~ ^[a-z][a-z0-9_]+$ ]] || { echo "[new-service] db-schema must be snake_case ([a-z][a-z0-9_]+)" >&2; exit 2; }
# Convention guard: PGUSER is set to "<schema>_svc" in .env.example. If
# the schema itself ended in _svc the resulting role would be foo_svc_svc.
# (Substitution side-effect of __DB_SCHEMA__ matching greedily.)
[[ ! "${SCHEMA}" =~ _svc$ ]] || { echo "[new-service] db-schema must not end in '_svc' (PGUSER would become <schema>_svc — double suffix)" >&2; exit 2; }
[[ "${PORT}"   =~ ^[0-9]+$ ]]          || { echo "[new-service] default-port must be a positive integer" >&2; exit 2; }
[[ "${PORT}" -ge 1024 && "${PORT}" -le 65535 ]] || { echo "[new-service] port must be 1024..65535" >&2; exit 2; }

if [[ -n "${TOKEN_PREFIX}" ]]; then
  [[ "${TOKEN_PREFIX}" =~ ^[a-z]{2,4}$ ]] || { echo "[new-service] --prefix must be 2-4 lowercase letters" >&2; exit 2; }
fi
if [[ "${WITH_AUTH}" == "1" && -z "${TOKEN_PREFIX}" ]]; then
  echo "[new-service] --with-auth requires --prefix=<2-4 lowercase letters>" >&2; exit 2
fi
if [[ -z "${DESC}" ]]; then
  echo "[new-service] no description given — README.md and package.json will use a placeholder; please replace before first commit" >&2
  DESC="${NAME} (description pending)"
fi

# --- locations ----------------------------------------------------------
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SKEL="${HERE}/templates/service-skeleton"
TARGET="${HOME}/projects/${NAME}"
OPTIONAL_AUTH="${SKEL}/_optional/auth/migration.sql"

if [[ ! -d "${SKEL}" ]]; then
  echo "[new-service] skeleton missing at ${SKEL}" >&2; exit 1
fi
if [[ -e "${TARGET}" ]]; then
  echo "[new-service] target already exists: ${TARGET}" >&2; exit 1
fi

echo "[new-service] copying skeleton → ${TARGET}"
mkdir -p "${TARGET}"
# rsync preserves perms (incl. +x on scripts/) and is more predictable than cp -r.
# _optional/ is excluded so the bare service stays minimal — opt-ins are
# pulled in below per --with-* flag.
rsync -a \
  --exclude='.git' --exclude='node_modules' --exclude='dist' \
  --exclude='_optional' \
  "${SKEL}/" "${TARGET}/"

# --- placeholder substitution ------------------------------------------
echo "[new-service] substituting placeholders"
escaped_desc="${DESC//\//\\/}"   # description may contain slashes
escaped_prefix="${TOKEN_PREFIX//\//\\/}"  # safe even if empty

substitute() {
  local file="$1"
  sed -i \
    -e "s|__SERVICE_NAME__|${NAME}|g" \
    -e "s|__DB_SCHEMA__|${SCHEMA}|g" \
    -e "s|__DEFAULT_PORT__|${PORT}|g" \
    -e "s|__SERVICE_DESC__|${escaped_desc}|g" \
    -e "s|__TOKEN_PREFIX__|${escaped_prefix}|g" \
    "${file}"
}

# We touch every non-binary file. Limit scope to the file types we know exist.
find "${TARGET}" -type f \
  \( -name '*.md' -o -name '*.json' -o -name '*.ts' -o -name '*.cjs' \
     -o -name '*.sql' -o -name '*.sh' -o -name '*.yml' -o -name '*.yaml' \
     -o -name '*.toml' -o -name '.env.example' -o -name '.gitignore' \) \
  -print0 \
| while IFS= read -r -d '' f; do
    substitute "$f"
  done

# --- opt-in: --with-auth ------------------------------------------------
if [[ "${WITH_AUTH}" == "1" ]]; then
  if [[ ! -f "${OPTIONAL_AUTH}" ]]; then
    echo "[new-service] --with-auth requested but ${OPTIONAL_AUTH} missing" >&2
    exit 1
  fi
  AUTH_DEST="${TARGET}/db/migrations/002_auth.sql"
  if [[ -e "${AUTH_DEST}" ]]; then
    echo "[new-service] refusing to overwrite ${AUTH_DEST}" >&2
    exit 1
  fi
  echo "[new-service] copying optional auth migration → db/migrations/002_auth.sql"
  cp "${OPTIONAL_AUTH}" "${AUTH_DEST}"
  substitute "${AUTH_DEST}"
fi

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

  1) Provision the ${SCHEMA} schema + service-user in infra-postgres
     (idempotent; password via SVC_PASSWORD env, stdin, or interactive
     prompt — never as a CLI arg, to keep it out of bash history):

       SVC_PASSWORD='<>=16 chars>' \\
         bash ~/projects/infra-postgres/scripts/add-service-schema.sh \\
              ${SCHEMA} ${SCHEMA}_svc ecosystem

     Then put the same password into the new service's .env
     (PGPASSWORD).

  2) cd ${TARGET}
     cp .env.example .env       # fill PGPASSWORD with the new service-user's pwd
     pnpm install
     pnpm migrate
     pnpm build
     pnpm test                  # vitest passes with the skeleton's smoke test

EOF

if [[ "${WITH_AUTH}" == "1" ]]; then
  cat <<EOF
  2a) Auth opt-in is active. Next steps:
      - Implement src/auth.ts based on BBE-DBE/ip-pool-api/src/auth.ts
        (replace token-prefix "iplk_" with "${TOKEN_PREFIX}_").
      - Add scripts/bootstrap-key.sh + bootstrap-key.mjs (same source).
      - Mint the first key:  bash scripts/bootstrap-key.sh
      - Reserve the prefix in
        api-standards/templates/service-skeleton/_optional/auth/README.md
        (collision registry).

EOF
fi

cat <<EOF
  3) gh repo create BBE-DBE/${NAME} --private --source=. --push --description "${DESC}"

  4) PM2:  pm2 start ecosystem.config.cjs && pm2 save

EOF
