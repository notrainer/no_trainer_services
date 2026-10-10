# Vulnerable Containers for security testing

All containers here are vulnerable by design and belong in an isolated lab.

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
runs. Each image also has a full commit-SHA tag and source/revision labels.
The publication script stops on the first failed build or push. Run its checks
without building or publishing anything:

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

