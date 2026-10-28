# Dockerized Web App with PostgreSQL

A small Flask web app packaged as a Docker image and run alongside PostgreSQL with Docker Compose. Each request to the home page increments a counter stored in the database. This project practices image builds, service networking, environment-based configuration, health checks, and persistent volumes.

## Architecture

```mermaid
flowchart LR
    Browser["Browser on this computer"] -->|"http://localhost:5000"| App["Flask app container"]
    App -->|"Compose network, port 5432"| DB["PostgreSQL container"]
    DB --> Volume["Named volume: postgres_data"]
```

The app is published only on the local machine at `127.0.0.1`. PostgreSQL is not published to the host; the app reaches it by the Compose service name `db`. The named volume keeps database data when containers are recreated.

## Prerequisites

- Docker Engine with the Docker Compose plugin, or Docker Desktop.
- A terminal opened in this project directory.

## Configure and run

1. Create a local environment file from the example:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and replace `POSTGRES_PASSWORD` with a password for this local demo. `.env` is ignored by Git; do not commit real credentials.
3. Build the app image and start both services:

   ```bash
   docker compose up --build -d
   ```

4. Open <http://<localhost-ip-address>:5000>. Refresh the page to see the counter increase.
5. Check the app's database-aware health endpoint:

   ```bash
   curl http://<localhost-ip-address>:5000/health
   ```

   Expected response: `{"database":"connected","status":"ok"}`.

## Environment variables

| Variable | Purpose | Example |
|---|---|---|
| `APP_PORT` | Host port for the app; it remains bound to localhost | `5000` |
| `POSTGRES_DB` | Database created by the PostgreSQL image | `sample_app` |
| `POSTGRES_USER` | Database user created by the PostgreSQL image | `appuser` |
| `POSTGRES_PASSWORD` | Password for that database user | Set a private local value in `.env` |

Compose reads `.env` for interpolation and passes the database settings to the app as environment variables. Keep your actual `.env` private; `.env.example` documents the required variables without containing a personal credential.

## Useful commands

```bash
docker compose ps                 # Show service state and health
docker compose logs -f app        # Follow app logs
docker compose logs -f db         # Follow PostgreSQL logs
docker compose down               # Stop and remove containers/network; keep database volume
docker compose down -v            # Also delete the database volume and its data
```

Use `docker compose down -v` only when you are okay losing the saved page counter and database contents.

## What to explore next

- Change the app text and rebuild the image.
- Change `APP_PORT` in `.env` and visit the new local port.
- Stop and recreate the containers, then confirm the counter remains because the named volume persists.
- Add a database backup and restore procedure.
- Later, add a reverse proxy, CI image build, and deployment to an EC2 host.

## Lessons learned

Record what you learn here as you complete the project: how containers communicate, how Compose passes configuration, how health checks control startup order, and how a named volume preserves database state.
