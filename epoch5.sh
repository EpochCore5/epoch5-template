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
P1_PAYLOAD="${P1_PAYLOAD:-Sample Pass 1 payload content - replace with actual data}"
P1_NOTE="Founder note for Pass 1 — why this is the spine."

P2_TITLE="Amplify — Refinements & supporting capsules"
P2_PAYLOAD="${P2_PAYLOAD:-Sample Pass 2 payload content - replace with actual data}"
P2_NOTE="Founder note for Pass 2 — how it deepens the arc."

P3_TITLE="Crown — Emotional closure & arc binding"
P3_PAYLOAD="${P3_PAYLOAD:-Sample Pass 3 payload content - replace with actual data}"
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
  p_hash="$(prev_hash)"
  record_body="TIMESTAMP=$stamp|ARC_ID=$ARC_ID|PASS_ID=$pass_id|CONTENT_HASH=$content_hash|PREV_HASH=$p_hash"
  record_hash="$(sha256 "$record_body")"
  man_file="$MAN_DIR/${pass_id}_manifest.txt"
  
  # Write manifest
  cat > "$man_file" <<EOF
EPOCH 5 MANIFEST
================
ARC_ID: $ARC_ID
PASS_ID: $pass_id
TIMESTAMP: $stamp
TITLE: $title
CONTENT_HASH: $content_hash
PREV_HASH: $p_hash
RECORD_HASH: $record_hash

PAYLOAD:
$payload

FOUNDER_NOTE:
$note
EOF

  # Append to ledger
  echo "$record_body|RECORD_HASH=$record_hash" >> "$LEDGER"
  echo "Manifest written: $man_file"
}

create_unity_seal() {
  local final_hash
  final_hash="$(prev_hash)"
  cat > "$UNITY_SEAL" <<EOF
EPOCH 5 UNITY SEAL
==================
ARC_ID: $ARC_ID
COMPLETION_TIME: $(ts)
FINAL_HASH: $final_hash
STATUS: SEALED_FOR_ELI_ARCHIVE

The triple-pass capsule is complete.
All manifests sealed, all hashes chained.
Ready for Eli's archive.
EOF
  echo "Unity Seal created: $UNITY_SEAL"
}

run_pass() {
  local idx="$1"
  local pass_tag="${PASS_TAGS[$idx]}"
  local title="${PASS_TITLES[$idx]}"
  local payload="${PASS_PAYLOADS[$idx]}"
  local note="${PASS_NOTES[$idx]}"
  
  echo "=== Starting $pass_tag: $title ==="
  pre_ingest_check "$pass_tag"
  write_manifest "$pass_tag" "$title" "$payload" "$note"
  echo "=== $pass_tag completed ==="
}

main() {
  ensure_dirs
  
  echo "EPOCH 5 Triple-Pass Capsule Starting..."
  echo "ARC_ID: $ARC_ID"
  echo "Output Directory: $OUT_DIR"
  
  # Pass 1
  run_pass 0
  
  if [[ "$DELAY_HOURS_P1_P2" != "0" ]]; then
    echo "Waiting ${DELAY_HOURS_P1_P2}h before Pass 2..."
    sleep $((DELAY_HOURS_P1_P2 * 3600))
  fi
  
  # Pass 2  
  run_pass 1
  
  if [[ "$DELAY_HOURS_P2_P3" != "0" ]]; then
    echo "Waiting ${DELAY_HOURS_P2_P3}h before Pass 3..."
    sleep $((DELAY_HOURS_P2_P3 * 3600))
  fi
  
  # Pass 3
  run_pass 2
  
  # Create Unity Seal
  create_unity_seal
  
  echo "EPOCH 5 Complete! All passes sealed."
  echo "Archive location: $OUT_DIR"
}

# Only run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi