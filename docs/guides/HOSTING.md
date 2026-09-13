# Orville Small-Team Production Hosting

## Summary

This deployment uses a modular monolith: one Orville API container, one managed-by-Compose SQLite volume, and a Caddy reverse proxy that terminates HTTPS. The API is not exposed directly to the public network. This topology is intended for a solo developer or small team with predictable early traffic and a low operations budget.

## Topology

```text
Internet -> Caddy (80/443, automatic HTTPS) -> Orville API (private Docker network) -> SQLite volume
                                                        \\-> artifacts in the same persistent volume
```

| Component | Responsibility | Failure/recovery boundary |
|---|---|---|
| Caddy | TLS termination, compression, access logs, reverse proxy | Recreated from image; certificates persist in `caddy-data` |
| Orville API | Application and authenticated API routes | Rebuilt from source; data persists in `orville-data` |
| SQLite | Durable checkpoints and artifacts for one API instance | Back up the volume/database before upgrades |

## First deployment

1. Provision a small Linux host with Docker Engine and Docker Compose v2. Point the DNS A/AAAA record for the selected domain at the host.
2. Copy `.env.production.example` to `.env.production`, replace the API token with a high-entropy secret, and set `ORVILLE_DOMAIN` to the real DNS name. Do not commit `.env.production`.
3. Review `deploy/Caddyfile` and verify the domain value is supplied through the Compose environment.
4. Start the stack with `docker compose up -d --build`. Caddy will request certificates after DNS and ports 80/443 are reachable.
5. Verify the authenticated endpoint: `curl -H "Authorization: Bearer YOUR_TOKEN" https://YOUR_DOMAIN/api/v1/health`.

## Backup and recovery

Run `powershell -ExecutionPolicy Bypass -File .\\deploy\\backup.ps1` from the deployment directory. Copy the resulting database files to storage outside the host and periodically perform a restore test. To restore, stop the stack, replace the database in the persistent volume with a verified backup, and start the stack again.

## Operational rules

Keep one API replica while SQLite is the storage backend. Do not scale the API horizontally without moving checkpoint and artifact state to a shared database and object store. Restrict host SSH access, apply operating-system updates, monitor disk space, and retain Caddy logs. Rotate `ORVILLE_API_TOKEN` by updating `.env.production` and recreating the API container.

## Upgrade and rollback

Create a backup before deployment. Pull or build the new image, run `docker compose up -d --build`, and verify `/api/v1/health`. If validation fails, restore the prior source/image and database backup, then repeat the health check.

## Explicit limitations

This is a single-host topology. It does not provide multi-region failover, multi-user identity and authorization, distributed rate limiting, or zero-downtime migrations. Those capabilities should be added only when measured requirements justify the operational cost.
