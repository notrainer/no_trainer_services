#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "${1:-}" != "" && "${1:-}" != "--push" ]]; then
  echo "Usage: $0 [--push]" >&2
  exit 2
fi

owner=$(printf '%s' "${GITHUB_REPOSITORY_OWNER:-notrainer}" | tr '[:upper:]' '[:lower:]')
registry="${REGISTRY:-ghcr.io/$owner}"
repository="${GITHUB_REPOSITORY:-notrainer/no_trainer_services}"
revision="${GITHUB_SHA:-$(git rev-parse HEAD)}"
tags=("$revision")
if [[ -n "${TAG:-}" && "${TAG:-}" != latest && "${TAG:-}" != "$revision" ]]; then
  tags+=("$TAG")
fi
tags+=(latest)

for service in dns ldap mail postgres samba vsftpd; do
  image="$registry/no_trainer_$service"
  build_tags=()
  for tag in "${tags[@]}"; do
    build_tags+=(-t "$image:$tag")
  done
  echo "Building $image..."
  podman build --pull=always --no-cache -f "$service/Containerfile" \
    --label "org.opencontainers.image.source=https://github.com/$repository" \
    --label "org.opencontainers.image.revision=$revision" \
    "${build_tags[@]}" "$service"
  if [[ "${1:-}" == "--push" ]]; then
    for tag in "${tags[@]}"; do
      podman push "$image:$tag"
    done
  fi
done

echo "All six containers have been built."
