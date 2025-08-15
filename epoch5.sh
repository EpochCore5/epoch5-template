#!/usr/bin/env bash
# EPOCH 5 — One-shot Triple-Pass Capsule
# Purpose: Run EPOCH5 as a single script that seals Pass 1, then Pass 2 and Pass 3 with safe delays,
#          chaining provenance, hashes, and a final Unity Seal into Eli’s archive.

set -euo pipefail

########################################
# INPUT — PASTE YOUR CONTENT HERE
########################################

ARC_ID="EPOCH5-M1"

P1_TITLE="Anchor — Core walls-off revelations"
read -r -d '' P1_PAYLOAD <<'EOF'
[PASTE PASS 1 PAYLOAD HERE]
EOF
P1_NOTE="Founder note for Pass 1 — why this is the spine."

P2_TITLE="Amplify — Refinements & supporting capsules"
read -r -d '' P2_PAYLOAD <<'EOF'
[PASTE PASS 2 PAYLOAD HERE]
EOF
P2_NOTE="Founder note for Pass 2 — how it deepens the arc."

P3_TITLE="Crown — Emotional closure & arc binding"
read -r -d '' P3_PAYLOAD <<'EOF'
[PASTE PASS 3 PAYLOAD HERE]
EOF
P3_NOTE="Founder note for Pass 3 — the connective seal for Eli."

DELAY_HOURS_P1_P2="${DELAY_HOURS_P1_P2:-6}"
DELAY_HOURS_P2_P3="${DELAY_HOURS_P2_P3:-6}"

########################################
# CONFIG
########################################
OUT_DIR="./archive/EPOCH5"
MAN_DIR="$OUT_DIR/manifests"
LEDGER="$OUT_DIR/ledger.log"
HEARTBEAT="$OUT_DIR/heartbeat.log"
INCOMING_TIDE="$OUT_DIR/incoming_tide.log"
UNITY_SEAL="$OUT_DIR/unity_seal.txt"

PASS_TAGS=("E5-P1" "E5-P2" "E5-P3")
PASS_TITLES=("$P1_TITLE" "$P2_TITLE" "$P3_TITLE")
PASS_PAYLOADS=("$P1_PAYLOAD" "$P2_PAYLOAD" "$P3_PAYLOAD")
PASS_NOTES=("$P1_NOTE" "$P2_NOTE" "$P3_NOTE")

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

sha256() {
  if command -v openssl >/dev/null 2>&1; then
    printf "%s" "$1" | openssl dgst -sha256 | awk '{print $2}'
  elif command -v shasum >/dev/null 2>&1; then
    printf "%s" "$1" | shasum -a 256 | awk '{print $1}'
  else
    echo "Need openssl or shasum" >&2; exit 1
  fi
}

ensure_dirs() {
  mkdir -p "$OUT_DIR" "$MAN_DIR"
  touch "$LEDGER" "$HEARTBEAT" "$INCOMING_TIDE"
}

prev_hash() {
  local last
  last=$(tac "$LEDGER" | grep -m1 "RECORD_HASH=" || true)
  [[ -z "$last" ]] && printf "%064d" 0 || echo "$last" | sed -E 's/.*RECORD_HASH=([0-9a-f]+).*/\1/'
}

heartbeat() {
  echo "
$(ts) | ARC=$ARC_ID | HEARTBEAT | PASS=$1" >> "$HEARTBEAT"
}

pre_ingest_check() {
  [[ -w "$LEDGER" ]] || { echo "Guard: ledger not writable"; exit 1; }
  heartbeat "$1"
}

write_manifest() {
  local pass_id="$1" title="$2" payload="$3" note="$4"
  local stamp content_hash p_hash record_body record_hash man_file
  stamp="$(ts)"
  content_hash="$(sha256 "$ARC_ID|$pass_id|$stamp|$title|$payload|$note")"