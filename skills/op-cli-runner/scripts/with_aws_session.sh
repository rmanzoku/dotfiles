#!/usr/bin/env bash
# with_aws_session.sh — one 1Password approval per AWS job.
#
# Takes STS session credentials once through the profile's credential_process
# (one 1Password prompt), keeps them only in this process tree's environment,
# runs the command, and lets them vanish with the process. Nothing is written
# to disk. The 1Password authorization can then expire, and the Mac can be
# locked, without interrupting the job; only the STS expiry matters.
#
# Usage:
#   bash with_aws_session.sh --profile <aws-profile> [--duration <seconds>] -- <command> [args...]
#
#   --profile   AWS profile whose credential_process supplies the long-term key (required)
#   --duration  STS session length in seconds: 900..129600, default 14400 (4 hours)
#
# The command must not pass --profile to aws: an explicit --profile makes the
# AWS CLI ignore environment credentials, and every call would prompt again.
# Use AWS_PROFILE (exported here for region and other settings) instead.
set -euo pipefail

PROFILE=""
DURATION=14400
log() { printf '[aws-session] %s %s\n' "$(date '+%H:%M:%S')" "$*" >&2; }
usage() { sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --profile) PROFILE="${2:-}"; shift 2 ;;
    --duration) DURATION="${2:-}"; shift 2 ;;
    --) shift; break ;;
    -h|--help) usage ;;
    *) log "ERROR: unknown argument: $1"; usage ;;
  esac
done

[ -n "${PROFILE}" ] || { log "ERROR: --profile is required"; usage; }
[ $# -gt 0 ] || { log "ERROR: no command given after --"; usage; }
[[ "${DURATION}" =~ ^[0-9]+$ ]] && [ "${DURATION}" -ge 900 ] && [ "${DURATION}" -le 129600 ] \
  || { log "ERROR: --duration must be 900..129600 seconds"; exit 2; }
if [ -n "${AWS_SESSION_TOKEN:-}" ]; then
  log "ERROR: AWS_SESSION_TOKEN is already set; refusing to nest sessions"; exit 2
fi
for arg in "$@"; do
  case "${arg}" in
    --profile|--profile=*)
      log "ERROR: the command passes --profile, which makes the AWS CLI ignore the session credentials"; exit 2 ;;
  esac
done
command -v aws >/dev/null || { log "ERROR: aws CLI not found"; exit 2; }
command -v python3 >/dev/null || { log "ERROR: python3 not found"; exit 2; }

log "start: requesting an STS session token via profile ${PROFILE} for ${DURATION}s (expect one 1Password prompt)"
JSON="$(aws --profile "${PROFILE}" sts get-session-token --duration-seconds "${DURATION}" --output json)" \
  || { log "failed: sts get-session-token did not return credentials"; exit 1; }
# Parse in one place and keep the values out of argv; the JSON never leaves this process.
{ read -r AWS_ACCESS_KEY_ID; read -r AWS_SECRET_ACCESS_KEY; read -r AWS_SESSION_TOKEN; read -r EXPIRATION; } < <(
  printf '%s' "${JSON}" | python3 -c '
import json, sys
c = json.load(sys.stdin)["Credentials"]
for k in ("AccessKeyId", "SecretAccessKey", "SessionToken", "Expiration"):
    print(c[k])
'
)
unset JSON
[ -n "${AWS_SESSION_TOKEN}" ] || { log "failed: empty session token"; exit 1; }
export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
export AWS_PROFILE="${PROFILE}"   # region and other profile settings; env credentials resolve first, so credential_process is not consulted
log "session ready: expires ${EXPIRATION}; credentials live only in this process tree"

log "run: $*"
set +e
"$@"
RC=$?
set -e
log "end: exit ${RC} (session credentials discarded with this process)"
exit "${RC}"
