# No Trainer Services

**Deliberately vulnerable containers for security training.** Run them only in
an isolated, authorized lab. Credentials, open DNS recursion/zone transfers,
anonymous writable shares/FTP, SMTP relay settings and PostgreSQL trust access
are intentional exercise fixtures.

## Published images

The repository is now [`notrainer/no_trainer_services`](https://github.com/notrainer/no_trainer_services).
Update existing clones with:

```sh
git remote set-url origin git@github.com:notrainer/no_trainer_services.git
```

| Service | Image |
| --- | --- |
| DNS | `ghcr.io/notrainer/no_trainer_dns:latest` |
| LDAP | `ghcr.io/notrainer/no_trainer_ldap:latest` |
| Mail | `ghcr.io/notrainer/no_trainer_mail:latest` |
| PostgreSQL | `ghcr.io/notrainer/no_trainer_postgres:latest` |
| Samba | `ghcr.io/notrainer/no_trainer_samba:latest` |
| FTP | `ghcr.io/notrainer/no_trainer_vsftpd:latest` |

GitHub Actions publishes all six images on master pushes, tag pushes, and manual
runs. Each image gets `latest`, a full commit-SHA tag and source/revision labels.
Tag pushes also publish the Git tag. The script stops on the first failed build
or push. Run its checks without building or publishing anything:

```sh
python3 -m unittest discover -s tests -v
```

New GHCR packages default to private. Make them public or configure read-only
registry authentication, and verify access before changing deployment references.
Existing public `ghcr.io/b3n4kh/no_trainer_*` packages remain available for rollback;
repository transfer does not move those packages. No existing Samba package was
listed in the old account at migration time.

The current `notrainer/nmap-training` deployment uses its own fixture images and
does not consume these legacy services. No classroom deployment change is needed.

The sibling `../no_trainer_client` supplies a scanning desktop; `../no_trainer`
provides its browser portal. These are independent Git repositories.

## Structure and dependencies

| Directory | Service | Configuration | Ports |
| --- | --- | --- | --- |
| `dns/` | BIND DNS | `named.conf`, `db.example.com` | 53 TCP/UDP |
| `ldap/` | OpenLDAP | `ldap-config.ldif` | 389, 636 |
| `mail/` | Postfix SMTP | `main.cf` | 25 |
| `postgres/` | PostgreSQL | `init.sql` | 5432 |
| `samba/` | SMB file sharing | `smb.conf` | 137, 138, 139, 445 |
| `vsftpd/` | FTP | `vsftpd.conf` | 20, 21 |

Each directory is a standalone Containerfile build context. DNS, SMTP, SMB and
FTP use Ubuntu 26.04 and current distribution packages. PostgreSQL uses 18.6;
trust authentication is configured through its official entrypoint environment,
and initialization SQL runs only for an empty data directory. PostgreSQL 18 uses
versioned PGDATA under `/var/lib/postgresql`; mount that parent for persistence.
Existing older PostgreSQL volumes need a database upgrade or restore, not a
simple image replacement.

OpenLDAP remains on osixia 1.5.0, the latest stable v1 image. Its upstream has
[deprecated v1](https://github.com/osixia/container-openldap); a maintained
replacement requires a separate configuration migration. Do not treat a rebuild
of this training fixture as a security update to the LDAP runtime. Its custom
LDIF extends the image's default directory and creates the guest and weakuser
entries on fresh initialization.

## Build

Podman must be installed and running. The script stops on the first failure,
pulls current base images and bypasses cache so OS packages refresh:

```bash
REGISTRY=localhost TAG=updated ./build_containers.sh
```

This builds six local `localhost/no_trainer_<service>:updated` images. Build one:

```bash
podman build --pull=always --no-cache -t localhost/no_trainer_dns:updated dns
```

Publishing is explicit: after approval and a registry login, use
`./build_containers.sh --push`. `REGISTRY` defaults to `ghcr.io/notrainer` (or
the lowercased `GITHUB_REPOSITORY_OWNER` in CI). `TAG` adds another tag, such as
`updated` for local builds or a Git release tag in CI. Every build also creates
`latest` and a full commit-SHA tag. The GitHub workflow authenticates Podman and
publishes on master/tag pushes and manual runs. Use versioned tags or digests
when deploying and rolling back. A local rebuild does not push images.

## Validation and isolated use

```bash
bash -n build_containers.sh
shellcheck build_containers.sh
podman run --rm --network none --entrypoint named-checkconf localhost/no_trainer_dns:updated /etc/bind/named.conf
podman run --rm --network none --entrypoint testparm localhost/no_trainer_samba:updated -s
podman run --rm --network none --entrypoint postfix localhost/no_trainer_mail:updated check
```

Run startup/protocol checks in an internal Podman network with no published
ports. Verify DNS answers/zone loading, LDAP entries, SMTP readiness, PostgreSQL
initialization and fixture rows, SMB shares and FTP readiness. Anonymous FTP
uploads belong under `/upload`; the FTP chroot directory stays unwritable.
LDAP TLS certificates are generated at first boot; keep runtime state writable.
No full training-exercise regression suite is currently provided.

## Deployment checklist

1. Confirm the target lab is isolated and record each deployed image digest.
2. Use published `image:` references in deployment Compose; pull before restarting.
3. Back up persistent data. PostgreSQL major upgrades require an explicit migration
   plan; never attach an older database volume to PostgreSQL 18 directly.
4. Restart and verify each protocol's readiness and expected training fixtures.
5. On failure, restore previous image digests and compatible data backups. A
   PostgreSQL data upgrade cannot be rolled back by changing its image alone.

Never expose these services on public networks. Avoid default host port mappings;
connect authorized training clients through the private lab network instead.
