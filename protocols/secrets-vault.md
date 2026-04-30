# Secrets Vault — pattern

The pattern below is what every BBE-DBE service uses to keep secrets
out of source control AND survive a server-total-loss.

## What lives where

| Place | What | Recovery if lost |
|---|---|---|
| `~/projects/<service>/.env` | Live runtime secrets — DB password, API tokens, etc. | rebuilt from vault below |
| **Vault** (operator-controlled, off-server) | Master copy of every `.env`, plus the GPG master key, plus operator SSH keys | **Without this, total-server-loss = total data loss.** |
| GitHub Repo | Code only. `.env` is `.gitignored`; `.env.example` only documents keys with placeholders. | n/a |
| `infra-postgres/backups/` (host-local) | Daily encrypted DB dumps | re-uploaded off-site daily; see `backup-offsite.sh` |
| Off-site (Hetzner Storagebox) | Daily GPG-encrypted DB dumps | restore-drill verifies it works |

## Vault contents (minimum)

```
vault/
├── env/
│   ├── ip-pool-api.env
│   ├── infra-postgres.env
│   └── <new-services>.env       # one file per service
├── gpg/
│   ├── master-public.asc        # public key — share freely
│   ├── master-private.asc       # PRIVATE — operator-only
│   └── master-revocation.asc    # revoke certificate (for emergency)
├── ssh/
│   ├── netcup-server.key        # primary host SSH-key
│   ├── netcup-server.pub
│   └── storagebox.key           # Hetzner Storagebox SFTP-key
└── README.md                    # what each file does, restore procedure
```

## Vault medium

Operator decision (we **document** the choice but don't enforce it):

| Option | Pros | Cons |
|---|---|---|
| **1Password / Bitwarden vault** | rotation, sharing, audit log, mobile | requires trust in vendor |
| **Encrypted USB stick (LUKS) × 2** in two physical locations | offline, no vendor | manual sync, easy to forget |
| **YubiKey-encrypted file** in cloud storage | hardware-bound, cheap | YubiKey loss = full key loss |
| **`pass` (password-store) + git on private repo** | text-based, scriptable, GPG-native | requires GPG already set up |

**Default recommendation:** option 4 (`pass`). It uses the same GPG key
that encrypts off-site backups, so the vault is **one key away** from
recovery, and the repo can sit on a separate GitHub-private-repo or a
USB stick.

## GPG master key — setup once

```bash
# 1) Generate (operator workstation, NOT the server)
gpg --full-generate-key
#   - kind: ECC (sign + encrypt)
#   - curve: Curve25519
#   - expiry: 2 years (rotate via subkey afterwards)
#   - id: BBE-DBE Ops <ops@bbe-dbe.local>

# 2) Export
gpg --armor --export <KEYID> > master-public.asc
gpg --armor --export-secret-keys <KEYID> > master-private.asc
gpg --gen-revoke <KEYID> > master-revocation.asc

# 3) Place all three in the vault medium of choice (above).

# 4) Server side: import only the PUBLIC key.
gpg --import master-public.asc
gpg --edit-key <KEYID> trust    # set ultimate trust
```

The server can **encrypt** with the public key but cannot decrypt
without the private — that's the whole point.

## Restore drill (Pflicht: every 6 months)

1. Pretend the server is gone. Provision a fresh box.
2. From vault: `gpg --import master-private.asc`.
3. Pull a recent off-site backup, decrypt:
   ```bash
   gpg --decrypt ecosystem-YYYYMMDDTHHMMSSZ.sql.gz.gpg \
     | gunzip -c | psql -h localhost -U postgres -d ecosystem
   ```
4. Verify smoke tests pass (see each service's
   `docs/disaster-recovery.md`).
5. Record the result in `infra-postgres/STANDARDS.md` under
   "Letzter Drill".

## Anti-patterns

- ❌ Vault on the same machine as the server.
- ❌ GPG private key in any git repo, even private.
- ❌ Passing the GPG passphrase via env var on the server. (Encryption
  uses the public key — no passphrase needed server-side.)
- ❌ Single point of vault. Always **two** copies in two locations.
- ❌ Sharing the master private key with co-workers — issue subkeys
  per operator instead.
