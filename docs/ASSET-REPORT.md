# Asset Report — BBE-DBE / SSR-SFS

**Stand:** 2026-09-11 · **145 Repos** · generiert aus `registry/REGISTRY.yaml`

> Generiert von `scripts/build_registry.py`. Nicht von Hand editieren.
> Jede Bewertung unten ist aus dem Snapshot reproduzierbar — Regeln stehen im Skript.

## Wie gelesen wird

| Tier | Bedeutung | Was zu tun ist |
|---|---|---|
| `CORE` | Ratifizierte Foundation (SERVICES.yaml) | Halten, Version pinnen |
| `ACTIVE` | Push in den letzten 45 Tagen | Zu Ende bringen |
| `ASSET` | ≥7 Tage echte Historie, aber ruhend | **Bewusst entscheiden:** wiederbeleben oder stilllegen |
| `SEED` | Angefangen, <7 Tage Historie | Meist stilllegen |
| `DUMP` | Gesamte Historie <1 Stunde | Backup-Snapshot, kein Projekt — stilllegen |

`score` = Wiederverwendungswert 0–100: 35 Iterationstiefe + 30 Aktualität + 15 Doku + 10 sauberer Trunk + 10 ratifiziert.

---

## Bestand

| Tier | Repos | Anteil |
|---|---:|---:|
| `CORE` | 7 | 4% |
| `ACTIVE` | 44 | 30% |
| `ASSET` | 19 | 13% |
| `SEED` | 36 | 24% |
| `DUMP` | 39 | 26% |

### Nach Domäne

| Domäne | Repos | davon CORE+ACTIVE | Top-Asset |
|---|---:|---:|---|
| `agent-orchestration` | 20 | 9 | `pm-runner` (89) |
| `construction-ssr` | 20 | 11 | `ssr` (87) |
| `brand-site` | 18 | 2 | `taxonair` (66) |
| `analytics-tracking` | 14 | 4 | `geo-visibility` (88) |
| `content-cms` | 13 | 4 | `cloud-adam-eve` (86) |
| `infra-provisioning` | 12 | 7 | `port-registry` (91) |
| `identity-auth` | 11 | 4 | `zz-keychain` (81) |
| `hub-dashboard` | 10 | 2 | `company-hubs` (81) |
| `commerce` | 8 | 1 | `preowned-zabazingo` (79) |
| `lead-gen` | 7 | 2 | `Automotivequestionaire` (66) |
| `comms-messaging` | 6 | 3 | `bbe-mail` (88) |
| `security-tooling` | 3 | 0 | `bbe-security-scanner` (11) |
| `ai-routing` | 2 | 1 | `xbrain` (81) |
| `standards-governance` | 1 | 1 | `api-standards` (47) |

---

## Konsolidierung — was zusammengehört

Kuratiert, nicht geraten. Pro Cluster **ein** kanonisches Repo; der Rest ist Merge-Kandidat.

| Cluster | Kanonisch | Einfalten | Betroffene Repos |
|---|---|---:|---|
| `zabazingo` | `zabazingo-platform` | 8 | `zabazingo-website`, `zabazingo-hub`, `zabazingo-domains`, `zaba-zingo`, `zaba-zingo-yt`, `preowned-zabazingo`, `zz-keychain`, `zz-logo-db` |
| `agent-os` | `oktogen-os` | 8 | `AATP-OS`, `oktogen-aatp`, `Multiagentensysteme`, `sentinel`, `bbe-coord`, `oktogen-agents`, `CAWF`, `Neuraisphere` |
| `estate-hubs` | `bestbrands-hub` | 4 | `company-hubs`, `dbl9-hub`, `devhub`, `ideas-hub` |
| `off---set` | `offset-site` | 3 | `off---set`, `off---set-ideas`, `offset-studio` |
| `taxonair` | `taxonair` | 2 | `taxonair-hub`, `airscope-taxonair` |
| `geo` | `geo-visibility` | 2 | `geo-obs`, `bbe-geo-cities` |
| `parkpeak` | `parkpeak-v2` | 1 | `parkpeak` |
| `resonance` | `resonance-lab` | 1 | `resonance-sector` |
| `launchpad` | `launchpad-modules` | 1 | `LaunchPad` |
| `qr` | `oktogen-qr` | 1 | `qr` |
| `tracking` | `bbe-track-analytics` | 1 | `bbe-track` |
| `signit` | `signit-selfdemo` | 1 | `signit-admin-demo` |
| `identity` | `bbe-auth` | 1 | `auth00-agent` |

**34 Repos** lassen sich in **13 kanonische** zusammenführen.

---

## Die Assets


### CORE — ratifizierte Foundation (7)

| Score | Repo | Domäne | Sprache | Historie | Ruht seit | Aktion | Was es ist |
|---:|---|---|---|---:|---:|---|---|
| 91 | `port-registry` | infra-provisioning | TypeScript | 98d | 34d | **KEEP** | BPAP v1.0 source of truth — port allocation registry |
| 91 | `hetzner-api` | infra-provisioning | — | 98d | 34d | **KEEP** | BBE-DBE hetzner-api — see docs/BOOTSTRAP.md |
| 91 | `netcup-api` | infra-provisioning | TypeScript | 99d | 34d | **KEEP** | Headless Netcup provider-adapter service for the BBE-DBE ecosystem |
| 79 | `infra-postgres` | infra-provisioning | Shell | 50d | 84d | **KEEP** | Central Postgres for the BBE-DBE ecosystem (pinned, backed up, schema-isolated) |
| 76 | `server-bootstrap` | infra-provisioning | Shell | 36d | 97d | **KEEP** | Tier-aware Debian-13 server provisioning (public half: modules 00-70) |
| 47 | `api-standards` | standards-governance | Python | 10d | 123d | **KEEP** | Cross-service standards for the BBE-DBE ecosystem |
| 37 | `ip-pool-api` | infra-provisioning | TypeScript | 2d | 131d | **KEEP** | Headless, agent-first IP-pool service (BBE-DBE ecosystem) |

### ACTIVE — läuft gerade (44)

| Score | Repo | Domäne | Sprache | Historie | Ruht seit | Aktion | Was es ist |
|---:|---|---|---|---:|---:|---|---|
| 89 | `pm-runner` | agent-orchestration | TypeScript | 105d | 3d | **KEEP** | Auto-restart daemon for MAOF workers. Subscription-poll mode default, optional API-key f… |
| 89 | `bbe-coord` | agent-orchestration | Shell | 129d | 4d | **MERGE** | Multi-agent coordination system (BBE-DBE) |
| 88 | `geo-visibility` | analytics-tracking | TypeScript | 72d | 9d | **KEEP** | GEO / AI Visibility Tool — misst Marken-Sichtbarkeit in KI-Antworten (ChatGPT/Claude/Gem… |
| 88 | `bbe-mail` | comms-messaging | Rust | 107d | 10d | **KEEP** | Independent agent-first multi-tenant mail platform (BBE proprietary). Mono-repo with dep… |
| 87 | `ssr` | construction-ssr | HTML | 67d | 11d | **KEEP** | SSR — Serielle Fassadensanierung: ausfuehrender Betrieb (montiert SMS-Wandmodule) |
| 86 | `cloud-adam-eve` | content-cms | JavaScript | 102d | 14d | **KEEP** | cloud.adam---eve.com — per-user kDrive cloud storage · admin/stats · PM with 5-state wor… |
| 86 | `bbe-server-config` | infra-provisioning | Shell | 118d | 15d | **KEEP** | Server-hardening configs, decisions, drift-baselines for the BBE-DBE agent-first server … |
| 86 | `brydge-phase2` | agent-orchestration | — | 93d | 16d | **KEEP** | Brydge Phase 2 — Terminal-Access auf Cowork-Design + Chat + Advisory-Board |
| 81 | `digital-watermark` | content-cms | Python | 66d | 34d | **KEEP** | Self-hosted Open-Source digitales Wasserzeichen (C2PA + Meta Seal) + Schnueffler; Asset-… |
| 81 | `company-hubs` | hub-dashboard | HTML | 56d | 34d | **MERGE** | Per-company estate hubs (dbl9 style) for the BBE estate |
| 81 | `zz-keychain` | identity-auth | HTML | 67d | 34d | **MERGE** | ZZ Keychain — faithful ZABAZINGO password manager frontend, fully wired to Vaultwarden (… |
| 81 | `xbrain` | ai-routing | JavaScript | 64d | 34d | **KEEP** | KachelTabs — AI Tab Manager & Wissens-Browser (Chromium-Extension, Subscription-getriebe… |
| 81 | `10BX` | analytics-tracking | CSS | 85d | 34d | **KEEP** | 10BX — performance-marketing platform · 11xroas (paid ads) + 11xsocial (organic social) … |
| 80 | `bbe-auth` ⚠ | identity-auth | TypeScript | 103d | 1d | **SHIP** | Multi-tenant OIDC/OAuth2.1 identity provider (Welle-05-Identity, OKTOGEN add-on) |
| 78 | `signit-selfdemo` ⚠ | identity-auth | HTML | 87d | 8d | **SHIP** | sign.it self-presentation hub (56 doors) — staging on adam---eve.com |
| 78 | `bbe-ai-gateway` ⚠ | identity-auth | TypeScript | 88d | 10d | **SHIP** | BBE AI-Gateway — headless Multi-Modell-Router (Claude/Codex/Grok), Subscription-first, O… |
| 75 | `bbe-track-analytics` | analytics-tracking | JavaScript | 24d | 34d | **KEEP** | bbe-track collector + KI Session-Analyst + full-fidelity capture (self-hosted, dependenc… |
| 74 | `EcommerceSupplierAutomation` | commerce | TypeScript | 90d | 6d | **KEEP** | — |
| 73 | `oktogen-os` | agent-orchestration | TypeScript | 93d | 10d | **KEEP** | — |
| 72 | `bbe-skills` | agent-orchestration | JavaScript | 92d | 11d | **KEEP** | — |
| 71 | `oktogen-aatp` | agent-orchestration | TypeScript | 87d | 16d | **MERGE** | — |
| 71 | `oktogen-chat` ⚠ | comms-messaging | CSS | 62d | 34d | **SHIP** | OKTOGEN agent<->human chat backbone (Mattermost TE fleet template). 159=golden master. |
| 70 | `ssr-landingpage-v5` | construction-ssr | HTML | 32d | 19d | **KEEP** | — |
| 66 | `taxonair` | brand-site | HTML | 119d | 34d | **KEEP** | — |
| 66 | `design-value` | analytics-tracking | Python | 50d | 34d | **KEEP** | — |
| 66 | `agent-feeder` | agent-orchestration | HTML | 60d | 34d | **KEEP** | — |
| 66 | `bbe-frontend` | hub-dashboard | TypeScript | 99d | 34d | **KEEP** | — |
| 66 | `oktogen-qr` | content-cms | TypeScript | 67d | 34d | **KEEP** | — |
| 66 | `parkpeak-v2` | brand-site | HTML | 37d | 34d | **KEEP** | — |
| 66 | `Automotivequestionaire` | lead-gen | TypeScript | 145d | 34d | **KEEP** | — |
| 66 | `qr` | content-cms | — | 67d | 34d | **MERGE** | — |
| 66 | `immowert` | lead-gen | HTML | 41d | 34d | **KEEP** | — |
| 62 | `oktogen-agents` ⚠ | agent-orchestration | JavaScript | 82d | 14d | **MERGE** | — |
| 58 | `bbe-event-router` | agent-orchestration | Python | 5d | 11d | **KEEP** | OKTOGEN Event Router — minimaler Wecker (Cron-Poll): GitHub agent-ready/agent:idea Issue… |
| 57 | `ssr-angebot-engine` | construction-ssr | HTML | 21d | 30d | **KEEP** | — |
| 57 | `ssr-projekt-studio` | construction-ssr | HTML | 21d | 30d | **KEEP** | — |
| 56 | `ssr-prozesse` | construction-ssr | HTML | 20d | 31d | **KEEP** | — |
| 50 | `ssr-showcase-sdk` | construction-ssr | JavaScript | 16d | 34d | **KEEP** | — |
| 50 | `ssr-banking` | construction-ssr | JavaScript | 16d | 34d | **KEEP** | — |
| 50 | `ssr-copy-service` | construction-ssr | JavaScript | 16d | 34d | **KEEP** | — |
| 50 | `ssr-lohn` | construction-ssr | Python | 16d | 34d | **KEEP** | — |
| 48 | `bbe-wa-gateway` | comms-messaging | JavaScript | 0d | 26d | **KEEP** | WhatsApp-Anschluss des Hauses als lizenziertes OKTOGEN-Modul fuer den internen Gebrauch |
| 38 | `ssr-maschine` | construction-ssr | HTML | 4d | 26d | **KEEP** | — |
| 32 | `ssr-ts` | construction-ssr | JavaScript | 0d | 30d | **KEEP** | — |

### ASSET — echte Substanz, ruhend (hier liegt das ungenutzte Kapital) (19)

| Score | Repo | Domäne | Sprache | Historie | Ruht seit | Aktion | Was es ist |
|---:|---|---|---|---:|---:|---|---|
| 79 | `oktogen-cms` | content-cms | JavaScript | 58d | 45d | **REVIVE** | White-label multi-tenant headless CMS (Directus 11) — OKTOGEN Platform. Self-contained c… |
| 79 | `preowned-zabazingo` | commerce | JavaScript | 54d | 45d | **MERGE** | PreOwned by ZABAZINGO — TikTok/IG-style fashion resale storefront (static, wired to Merc… |
| 74 | `global-rank` | analytics-tracking | JavaScript | 33d | 66d | **REVIVE** | Global Rank — die belegte KI-Weltrangliste (Provenienz + Analyse + eigene Capability-Ach… |
| 64 | `zabazingo-hub` | hub-dashboard | HTML | 45d | 45d | **MERGE** | — |
| 60 | `Multiagentensysteme` | agent-orchestration | TypeScript | 34d | 161d | **MERGE** | Multi-Agent Operating Framework (MaOF) – KI-Agenten-System fuer skalierbare Digital-Roll… |
| 57 | `owl-router` | ai-routing | JavaScript | 20d | 82d | **REVIVE** | OWL — Open-Weight-LLM Router: freie Modelle (DeepSeek/Qwen/Llama/gpt-oss) ueber Claude C… |
| 56 | `MaxxiPower` | brand-site | HTML | 99d | 77d | **REVIVE** | — |
| 55 | `zaba-zingo` | brand-site | HTML | 79d | 82d | **MERGE** | — |
| 52 | `offset-site` | brand-site | HTML | 15d | 85d | **REVIVE** | off---set.com apex site + single deterministic OKTOGEN build pipeline |
| 49 | `gp-pm` | brand-site | JavaScript | 9d | 66d | **REVIVE** | gp-pm — Verbraucher-Hitliste Versicherer/Banken (Code-Slug; Brands geprellt.de + TBD). E… |
| 49 | `LaunchPad` | hub-dashboard | TypeScript | 73d | 102d | **MERGE** | — |
| 48 | `Health-Magazine-1000` | content-cms | HTML | 11d | 77d | **REVIVE** | HM1000 — 1000 Health-Magazine als agentengebautes SEO/GEO-Authority-Netz. #001 Pulsbreit… |
| 47 | `graydion` | lead-gen | Python | 9d | 77d | **REVIVE** | GRAYDION — Freemium-Bonitaetsanalyse (PSD2/Upload): 21-Merkmale-Ampel + Bankready-Score,… |
| 45 | `Neuraisphere` | agent-orchestration | TypeScript | 31d | 168d | **MERGE** | — |
| 42 | `devhub` | hub-dashboard | HTML | 18d | 77d | **MERGE** | — |
| 41 | `imgmf` | content-cms | HTML | 8d | 94d | **REVIVE** | anno.js — visueller Review-/Annotations-/Capture-Layer + KI-Workflow-Zentrale (IMGMF) |
| 41 | `CAWF` | agent-orchestration | TypeScript | 27d | 168d | **MERGE** | — |
| 31 | `bbe-voice` ⚠ | comms-messaging | TypeScript | 8d | 95d | **REVIVE** | Multi-tenant white-label voice gateway (TTS/STT), swappable engine provider-adapters — P… |
| 13 | `commerce-supremacy` ⚠ | commerce | Python | 11d | 160d | **REVIVE** | — |

### SEED — angefangen, dünn (36)

| Score | Repo | Domäne | Sprache | Historie | Ruht seit | Aktion | Was es ist |
|---:|---|---|---|---:|---:|---|---|
| 44 | `LEAD-GEN-SSR` | lead-gen | HTML | 6d | 70d | **ARCHIVE** | LEAD-GEN-SSR — SSR-Lead-Gen-Engine: Adresse -> amtliche NRW-Geodaten (DOP20/LoD2/ALKIS/B… |
| 35 | `bestbrands-hub` | hub-dashboard | HTML | 2d | 89d | **ARCHIVE** | Central Estate hub for hub.bestbrandseverywhere.com (verified-live surfaces + full domai… |
| 34 | `bbe-web-harvester` | analytics-tracking | Python | 0d | 84d | **ARCHIVE** | BBE Web Harvester — Websites -> bbe.harvest.v1 -> SQLite Wissens-DB + regelbasierte Bewe… |
| 33 | `ideas-hub` | content-cms | HTML | 0d | 88d | **MERGE** | Display surface for BBE ideas captured in the PM (machine-readable bbe.idea.v1, bestbran… |
| 31 | `agentpedia-wiki` | content-cms | Astro | 5d | 163d | **ARCHIVE** | AgentPedia.wiki — The Open Encyclopedia of AI Agents |
| 30 | `offset-studio` | brand-site | HTML | 0d | 100d | **MERGE** | Internal collaboration cockpit for demo.off---set.com (off---set CI) |
| 30 | `apex` | analytics-tracking | Python | 1d | 102d | **ARCHIVE** | APEX — Intelligence/Asset-Valuation Layer (Knowledge Graph, headless API-first) |
| 29 | `ssr-drone-pm` | construction-ssr | JavaScript | 2d | 54d | **ARCHIVE** | — |
| 29 | `liteprofil` | infra-provisioning | TypeScript | 0d | 106d | **ARCHIVE** | Digital business card platform — liteprofil.de (host: Hetzner lite-profil-server) |
| 29 | `sentinel` | agent-orchestration | JavaScript | 1d | 108d | **MERGE** | Sentinel — Autonomous, learning, auditable AI agent orchestrator. 5-layer architecture. … |
| 28 | `viral-workspace` | content-cms | TypeScript | 0d | 108d | **ARCHIVE** | Viral cloud-storage growth feature (Adam-Eve + Zabazingo). K-Factor >= 1.2 in 90d. Consu… |
| 28 | `nutrio` | lead-gen | TypeScript | 0d | 108d | **ARCHIVE** | NUTRIO — Central Engine fuer Ernaehrungs- & Habit-Coaching (Multi-Brand: ZZ + Adam-Eve).… |
| 28 | `question-engine` | infra-provisioning | TypeScript | 0d | 108d | **ARCHIVE** | Brand-agnostic Advisory-Board Question-Engine (MAOF). Multi-tenant, DSGVO, A/B-tests. Ho… |
| 27 | `bkw-platform` | agent-orchestration | HTML | 0d | 116d | **ARCHIVE** | BKW Platform — state-of-the-art comparison engine. Agent-first, API-first, plugin-based,… |
| 26 | `bbe-secrets-vault` | identity-auth | Shell | 1d | 130d | **ARCHIVE** | Tiny age-encrypted secret store for local agents. CLI: init/set/get/list/rotate/audit. A… |
| 26 | `kuberg-clone` | brand-site | TypeScript | 1d | 182d | **ARCHIVE** | Pilot Website Electric Bikes |
| 25 | `bbe-fork-control-plane` | agent-orchestration | HTML | 0d | 130d | **ARCHIVE** | Fork-control plane dashboard for the BBE-DBE multi-agent system. Five sign.it 1.0 module… |
| 25 | `signtrust` | identity-auth | TypeScript | 0d | 150d | **ARCHIVE** | Headless, API-first, agent-ready Digital Signature & Verification Core |
| 25 | `AATP-OS` | agent-orchestration | JavaScript | 0d | 168d | **MERGE** | AATP-OS — Agent Zero Protocol. Trust infrastructure for autonomous agent organizations. … |
| 25 | `automotive-onboarding-platform` | identity-auth | TypeScript | 0d | 179d | **ARCHIVE** | Automotive Onboarding Platform fuer OEMs und Zulieferer – React, Tailwind, shadcn/ui, Au… |
| 21 | `luescher-color-test` | lead-gen | JavaScript | 0d | 76d | **ARCHIVE** | — |
| 21 | `dbl9-hub` | hub-dashboard | HTML | 2d | 88d | **MERGE** | — |
| 21 | `design-stack` ⚠ | infra-provisioning | Shell | 0d | 95d | **ARCHIVE** | White-label self-hosted design-tool foundation (Penpot+Excalidraw+draw.io) — one bluepri… |
| 20 | `fassaden-iq` | construction-ssr | HTML | 0d | 82d | **ARCHIVE** | — |
| 18 | `signit-admin-demo` | identity-auth | JavaScript | 2d | 96d | **MERGE** | — |
| 17 | `shopify-connect` | commerce | HTML | 0d | 93d | **ARCHIVE** | — |
| 15 | `gotteswasser` | brand-site | HTML | 0d | 103d | **ARCHIVE** | — |
| 14 | `pyka` | brand-site | JavaScript | 0d | 103d | **ARCHIVE** | — |
| 14 | `litecard` | commerce | TypeScript | 0d | 104d | **ARCHIVE** | — |
| 13 | `11x` | analytics-tracking | — | 2d | 134d | **ARCHIVE** | — |
| 11 | `bbe-security-scanner` | security-tooling | Shell | 1d | 130d | **ARCHIVE** | — |
| 11 | `ia-trainingbox-project` | brand-site | HTML | 1d | 167d | **ARCHIVE** | — |
| 11 | `DropSet` | commerce | HTML | 1d | 167d | **ARCHIVE** | — |
| 10 | `bbe-worktree-toolkit` | security-tooling | Shell | 0d | 131d | **ARCHIVE** | — |
| 10 | `canva-adam-eve` | content-cms | JavaScript | 0d | 154d | **ARCHIVE** | — |
| 10 | `earth-moon` | brand-site | JavaScript | 0d | 155d | **ARCHIVE** | — |

### DUMP — Backup-Snapshots, keine Projekte (39)

| Score | Repo | Domäne | Sprache | Historie | Ruht seit | Aktion | Was es ist |
|---:|---|---|---|---:|---:|---|---|
| 53 | `bbe-leads` | lead-gen | JavaScript | 0d | 7d | **ARCHIVE** | bbe-leads — Lead-Eingang, Uebersicht, Bedarfsanalyse, Fragebogen und Upload fuer AGEN.OS… |
| 43 | `bitchat` | comms-messaging | — | 0d | 47d | **ARCHIVE** | bitchat — netzunabhaengiger BLE-Mesh-Betriebsfunk (Fork permissionlesstech/bitchat, Unli… |
| 41 | `ssr-verwaltung` | construction-ssr | HTML | 0d | 56d | **ARCHIVE** | SSR Verwaltungs-Cockpit — Intent-first Beschluss- & Governance-Konsole fuer Bau & Handwe… |
| 39 | `marketplace` | commerce | — | 0d | 5d | **ARCHIVE** | — |
| 36 | `sms` | construction-ssr | — | 0d | 78d | **ARCHIVE** | SMS — Sanieren mit System: Hersteller der Wandmodule fuer serielle Sanierung (Schwester:… |
| 35 | `base-stack` | comms-messaging | Shell | 0d | 79d | **ARCHIVE** | BBE base-stack: de-branded Mattermost TE + Chatwoot CE, one-command bootstrap |
| 34 | `ai-connect` | agent-orchestration | HTML | 0d | 84d | **ARCHIVE** | ai-connect — branded ai-value landing wrapping the live shell (Agent University eval fro… |
| 31 | `auth00-agent` | identity-auth | TypeScript | 0d | 98d | **MERGE** | auth00-agent — agent-native Login & Telemetrie. Tochter von bbe-auth (auth00). Agenten l… |
| 30 | `zz-logo-db` | content-cms | JavaScript | 0d | 99d | **MERGE** | ZZ Logo-DB — freie Logo-Datenbank (clean Assets) Modul. Code-only backup; cache/ und dat… |
| 30 | `upcloud-api` | infra-provisioning | TypeScript | 0d | 100d | **ARCHIVE** | Headless UpCloud provider-adapter (BBE-DBE) — GPU servers + Partner-API reselling. Mirro… |
| 29 | `pm-presentation` | agent-orchestration | HTML | 0d | 102d | **ARCHIVE** | PM-System Vorstellungsseite (claude-style) — Multi-Agent-Betriebssystem. Serviert :5622. |
| 29 | `oktogen-market` | agent-orchestration | — | 0d | 102d | **ARCHIVE** | OKTOGEN Marketplace (AI Agentic Agents) — cloud-asset monetization. Hybrid-at-module-lev… |
| 29 | `oktogen-vault` | identity-auth | HTML | 0d | 102d | **ARCHIVE** | OKTOGEN Vault — white-label multi-tenant Vaultwarden ops tree (scripts, compose, caddy, … |
| 28 | `notes-hub-v2` | content-cms | HTML | 0d | 108d | **ARCHIVE** | Notes-Hub V2 — Notion+Obsidian-Hybrid fuer Adam-Eve + Zabazingo |
| 27 | `ssr-neubau-angebot` | construction-ssr | TypeScript | 0d | 50d | **ARCHIVE** | — |
| 27 | `ssr-wiebusch-konsole` | construction-ssr | HTML | 0d | 50d | **ARCHIVE** | — |
| 27 | `ssr-shell` | construction-ssr | JavaScript | 0d | 50d | **ARCHIVE** | — |
| 27 | `ssr-partner-backend` | construction-ssr | HTML | 0d | 50d | **ARCHIVE** | — |
| 27 | `ssr-angebot-inbox` | construction-ssr | JavaScript | 0d | 50d | **ARCHIVE** | — |
| 26 | `saas-cost-wallet` | analytics-tracking | HTML | 0d | 117d | **ARCHIVE** | SaaS Cost Analyse Wallet — Cost-Tracking + Finance-Dashboard modules (5 views) |
| 26 | `launchpad-modules` | hub-dashboard | HTML | 0d | 117d | **ARCHIVE** | LaunchPad Modules — reusable headless static modules (CI, dashboards, status, costs, pip… |
| 25 | `zabazingo-platform` | hub-dashboard | JavaScript | 0d | 119d | **ARCHIVE** | ZABAZINGO complete platform mono-repo — brand landings, hubs, transfer service, concepts… |
| 25 | `resonance-sector` | analytics-tracking | CSS | 0d | 120d | **MERGE** | Resonance Lab — Creative Performance Sector (Internal). Kompaktere Variante der Resonanc… |
| 25 | `resonance-lab` | analytics-tracking | JavaScript | 0d | 120d | **ARCHIVE** | Resonance Lab — Creative Performance OS. Internal asset-analysis tool with intent-aware … |
| 25 | `zabazingo-website` | brand-site | HTML | 0d | 121d | **MERGE** | ZABA & ZINGO — don't believe everything. Scroll-Cinematic Brand-Site. v7 + 9 idee-Varian… |
| 25 | `off---set-ideas` | brand-site | HTML | 0d | 122d | **MERGE** | off---set IDeas — HTML-Prototypen + Brand-Video fuer off---set (CIPHER_CLONE, agen-os v3… |
| 25 | `off---set` | agent-orchestration | HTML | 0d | 122d | **MERGE** | off---set — Operator, not Marketer. Brand site for C-Level acquisition in Automotive/Mob… |
| 25 | `zaba-zingo-yt` | brand-site | JavaScript | 0d | 159d | **MERGE** | YouTube Music Channel Analyzer & Auto-Publisher — ZABA & ZINGO Brand Network |
| 22 | `bbe-track` | analytics-tracking | JavaScript | 0d | 70d | **MERGE** | — |
| 22 | `bbe-geo-cities` | analytics-tracking | JavaScript | 0d | 70d | **MERGE** | — |
| 22 | `airscope-taxonair` | brand-site | HTML | 0d | 70d | **MERGE** | — |
| 22 | `parkpeak` | brand-site | HTML | 0d | 71d | **MERGE** | — |
| 16 | `verified-purchase` | commerce | — | 0d | 96d | **ARCHIVE** | — |
| 16 | `emergency` | infra-provisioning | Shell | 0d | 97d | **ARCHIVE** | — |
| 16 | `geo-obs` | analytics-tracking | TypeScript | 0d | 98d | **MERGE** | — |
| 15 | `signup-guard` | identity-auth | JavaScript | 0d | 99d | **ARCHIVE** | — |
| 14 | `zabazingo-domains` | brand-site | — | 0d | 103d | **MERGE** | — |
| 12 | `taxonair-hub` ⚠ | hub-dashboard | HTML | 0d | 70d | **MERGE** | — |
| 10 | `bbe-sprint-machine` | security-tooling | Shell | 0d | 131d | **ARCHIVE** | — |

---

## ⚠ Offene Trunks (9)

Der Default-Branch ist ein Feature-Branch. Die Hauptarbeit wurde nie auf `main` gebracht —
jeder Klon landet auf halbfertigem Stand, und CI/Releases greifen ins Leere.

| Repo | Default-Branch | Tier |
|---|---|---|
| `bbe-auth` | `feat/T-AUTH-100-phase1-core-oidc` | ACTIVE |
| `signit-selfdemo` | `feat/signit-selfdemo-staging` | ACTIVE |
| `bbe-ai-gateway` | `feat/bbe-ai-gateway-p2` | ACTIVE |
| `oktogen-chat` | `feat/templatize-fleet` | ACTIVE |
| `oktogen-agents` | `feat/passport-registry-v0` | ACTIVE |
| `bbe-voice` | `feat/bbe-voice-p0` | ASSET |
| `design-stack` | `feat/design-stack-foundation` | SEED |
| `commerce-supremacy` | `feature/bootstrap-build-os` | ASSET |
| `taxonair-hub` | `feat/devhub-ops-hub2` | DUMP |

---

## Ohne Beschreibung (65)

Kein `description`-Feld. Für einen Agenten (und für dich in 3 Monaten) unsichtbar —
`Lookup-before-Build` kann darauf nicht greifen. Billigster Fix im ganzen Bestand.

| Repo | Tier | Score |
|---|---|---:|
| `EcommerceSupplierAutomation` | ACTIVE | 74 |
| `oktogen-os` | ACTIVE | 73 |
| `bbe-skills` | ACTIVE | 72 |
| `oktogen-aatp` | ACTIVE | 71 |
| `ssr-landingpage-v5` | ACTIVE | 70 |
| `taxonair` | ACTIVE | 66 |
| `design-value` | ACTIVE | 66 |
| `agent-feeder` | ACTIVE | 66 |
| `bbe-frontend` | ACTIVE | 66 |
| `oktogen-qr` | ACTIVE | 66 |
| `parkpeak-v2` | ACTIVE | 66 |
| `Automotivequestionaire` | ACTIVE | 66 |
| `qr` | ACTIVE | 66 |
| `immowert` | ACTIVE | 66 |
| `zabazingo-hub` | ASSET | 64 |
| `oktogen-agents` | ACTIVE | 62 |
| `ssr-angebot-engine` | ACTIVE | 57 |
| `ssr-projekt-studio` | ACTIVE | 57 |
| `ssr-prozesse` | ACTIVE | 56 |
| `MaxxiPower` | ASSET | 56 |
| `zaba-zingo` | ASSET | 55 |
| `ssr-showcase-sdk` | ACTIVE | 50 |
| `ssr-banking` | ACTIVE | 50 |
| `ssr-copy-service` | ACTIVE | 50 |
| `ssr-lohn` | ACTIVE | 50 |
| `LaunchPad` | ASSET | 49 |
| `Neuraisphere` | ASSET | 45 |
| `devhub` | ASSET | 42 |
| `CAWF` | ASSET | 41 |
| `marketplace` | DUMP | 39 |
| `ssr-maschine` | ACTIVE | 38 |
| `ssr-ts` | ACTIVE | 32 |
| `ssr-drone-pm` | SEED | 29 |
| `ssr-neubau-angebot` | DUMP | 27 |
| `ssr-wiebusch-konsole` | DUMP | 27 |
| `ssr-shell` | DUMP | 27 |
| `ssr-partner-backend` | DUMP | 27 |
| `ssr-angebot-inbox` | DUMP | 27 |
| `bbe-track` | DUMP | 22 |
| `bbe-geo-cities` | DUMP | 22 |
| `airscope-taxonair` | DUMP | 22 |
| `parkpeak` | DUMP | 22 |
| `luescher-color-test` | SEED | 21 |
| `dbl9-hub` | SEED | 21 |
| `fassaden-iq` | SEED | 20 |
| `signit-admin-demo` | SEED | 18 |
| `shopify-connect` | SEED | 17 |
| `verified-purchase` | DUMP | 16 |
| `emergency` | DUMP | 16 |
| `geo-obs` | DUMP | 16 |
| `signup-guard` | DUMP | 15 |
| `gotteswasser` | SEED | 15 |
| `zabazingo-domains` | DUMP | 14 |
| `pyka` | SEED | 14 |
| `litecard` | SEED | 14 |
| `11x` | SEED | 13 |
| `commerce-supremacy` | ASSET | 13 |
| `taxonair-hub` | DUMP | 12 |
| `bbe-security-scanner` | SEED | 11 |
| `ia-trainingbox-project` | SEED | 11 |
| `DropSet` | SEED | 11 |
| `bbe-worktree-toolkit` | SEED | 10 |
| `bbe-sprint-machine` | DUMP | 10 |
| `canva-adam-eve` | SEED | 10 |
| `earth-moon` | SEED | 10 |

---

## Nächste Aktion

| Aktion | Repos | Bedeutung |
|---|---:|---|
| **KEEP** | 41 | Bestand, nichts zu tun |
| **SHIP** | 4 | Aktiv, aber Trunk offen — Branch nach main mergen |
| **REVIVE** | 11 | Substanz vorhanden, ruhend — bewusst entscheiden |
| **MERGE** | 34 | In das kanonische Repo des Clusters einfalten |
| **ARCHIVE** | 55 | Stilllegen (GitHub-Archive, nicht löschen) |

---

_Regenerieren:_ `python3 scripts/build_registry.py`
