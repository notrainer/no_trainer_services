#!/bin/bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
owner=$(printf '%s' "${GITHUB_REPOSITORY_OWNER:-notrainer}" | tr '[:upper:]' '[:lower:]')
repository="${GITHUB_REPOSITORY:-notrainer/no_trainer_services}"
revision="${GITHUB_SHA:-$(git rev-parse HEAD)}"

for service in dns ldap mail postgres samba vsftpd; do
  image="ghcr.io/$owner/no_trainer_$service"
  echo "Building container for $service..."
  podman build -f "$service/Containerfile" \
    --label "org.opencontainers.image.source=https://github.com/$repository" \
    --label "org.opencontainers.image.revision=$revision" \
    -t "$image:latest" -t "$image:$revision" "$service"
  podman push "$image:latest"
  podman push "$image:$revision"
  echo "Finished building container for $service"
done

echo "All six containers have been built and published."

