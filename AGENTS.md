# Working on No Trainer Services

This repository contains six independent, intentionally vulnerable lab images:
`dns/` (BIND), `ldap/` (OpenLDAP), `mail/` (Postfix), `postgres/` (PostgreSQL),
`samba/` (SMB), and `vsftpd/` (FTP). Each directory has a Containerfile plus its
configuration/fixtures and is its own build context. Sibling repositories are
`../no_trainer` (portal) and `../no_trainer_client` (scanner desktop).

Preserve deliberate weak credentials, DNS recursion/zone transfers, SMTP relay,
FTP/SMB access and database trust fixtures unless a task explicitly changes an
exercise. Isolation is the security boundary. Do not add public port mappings or
scan/send traffic outside the authorized lab. Inspect local changes before edits.

`build_containers.sh` lists the six services, uses `set -euo pipefail`, pulls bases
and disables cache. It builds only unless passed `--push`; `REGISTRY` selects
the registry and `TAG` adds a tag alongside `latest` and the full commit SHA.
Use `REGISTRY=localhost TAG=updated ./build_containers.sh` for verification.
`.github/workflows/container_build.yaml` logs into GHCR with Podman and publishes
`latest`, the full commit SHA, and a release tag on tag pushes. Do not push or
trigger releases without authorization. Build individual services with `podman build --pull=always
--no-cache -t localhost/no_trainer_<service>:updated <service>`.

Ubuntu services use 26.04. PostgreSQL uses 18.6 and official entrypoint variables
for trust authentication; do not write files into PGDATA during the image build.
Its `init.sql` only applies to fresh volumes. PostgreSQL 18 stores versioned data
under `/var/lib/postgresql`; older data needs an explicit upgrade/restore plan.
OpenLDAP's osixia 1.5.0 base is the latest stable v1 but deprecated upstream;
changing providers requires verifying bootstrap LDIF, TLS, startup and data paths.

Validate shell edits with `bash -n build_containers.sh` and
`shellcheck build_containers.sh`. Check BIND configuration/zone, Samba with
testparm, Postfix with postfix check, and startup/protocol readiness for all
changed images. Use temporary containers on an internal network with no host
ports; remove only test resources you created. Verify PostgreSQL fixture rows
and LDAP guest/weakuser entries after fresh initialization.

Keep Podman compatibility, small changes and readable build files. Update README
and deployment/rollback guidance when bases, fixtures or commands change.
Deployment Compose uses published images, never implicit builds. Ask before
publishing, deploying, destructive data operations or public exposure. Report
which images built, what health checks passed, and upstream exceptions.
