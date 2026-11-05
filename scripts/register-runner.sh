#!/bin/sh
# Linux host with GitLab Runner installed. Authentication token comes from the GitLab UI.
set -eu
: "${CI_SERVER_URL:?Set the HTTPS URL of work GitLab}"
: "${RUNNER_TOKEN:?Supply the runner authentication token securely}"
: "${PILOT_IMAGE:?Set the pullable image with its sha256 digest}"
case "$PILOT_IMAGE" in *@sha256:*) ;; *) echo 'Image must include a digest' >&2; exit 2;; esac
case "${1:-}" in
  discovery) set -- ;;
  writer) : "${STATE_DIR:?Set the absolute Linux host reservation directory}"
          test -f "$STATE_DIR/.pilot-state-volume"
          set -- --docker-volumes "$STATE_DIR:/var/lib/renovate-reservations:rw" ;;
  *) echo 'Usage: register-runner.sh discovery|writer' >&2; exit 2 ;;
esac
CI_SERVER_TOKEN="$RUNNER_TOKEN" gitlab-runner register --non-interactive --executor docker --docker-image "$PILOT_IMAGE" "$@"
