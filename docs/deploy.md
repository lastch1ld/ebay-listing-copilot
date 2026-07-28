# Deploying to Hetzner

This mirrors the same Docker + Caddy + Hetzner pattern used for this
project's sibling (the Wix tourism-site generator), which already runs on
this server and already owns host ports 80/443 via its own Caddy instance.
**This app does not run a second Caddy** — two processes cannot both bind
80/443 on the same host regardless of domain — it instead joins that
existing Caddy's reverse proxy over a shared Docker network.

**Read this before exposing the app publicly:** the app's default design is
local-only, loopback-bound, single-user, with no login of its own (see
[`docs/privacy.md`](privacy.md) and `AGENTS.md`). Deploying it to a public
server is a real change to that threat model — anyone who reaches the URL
without credentials could trigger real eBay actions or burn your OpenAI
quota. This setup puts **Caddy Basic Auth in front of everything** (except
`/api/health`) as the minimum viable gate. Do not remove that without adding
an equivalent control.

## What's in the repo for this

- `Dockerfile` — multi-stage: builds the frontend, then serves it as static
  files from the same FastAPI process that serves `/api/*` (single
  container, single port, `8000` internally).
- `docker-compose.yml` — one `app` service. It publishes **no host port at
  all**; it joins an external Docker network named `edge` so the server's
  existing shared Caddy can reach it by container name
  (`ebay-listing-copilot-app`), avoiding both the port-overlap problem and
  the Docker networking pitfall where a `127.0.0.1`-bound host port isn't
  reachable from a sibling container's bridge network anyway.
- `Caddyfile.snippet.example` — the site block to append to the **existing**
  shared Caddyfile (not a standalone Caddy config for this app). Full
  instructions are in the file itself.
- `.github/workflows/deploy.yml` — on push to `master` (path-filtered), SSHes
  in and lets the server's forced command do `git pull && docker compose up
  -d --build`, then polls `/api/health`.

## One-time server bootstrap (needs your own hands-on-keyboard)

I have no SSH access to your Hetzner box from this session, so these steps
are for you to run yourself, from a machine you trust with that server.

1. **Create the shared Docker network**, if it doesn't already exist:
   ```bash
   docker network create edge
   ```
2. **Join the existing shared Caddy to that network too.** In the tourism
   generator's `docker-compose.yml`, add `edge` (as `external: true`) to the
   `caddy` service's `networks:` list alongside whatever it already uses.
3. **Point DNS** at the server: an A record for your chosen domain (e.g.
   `listing-copilot.yourdomain.com`).
4. **Generate the Basic Auth password hash:**
   ```bash
   docker run --rm caddy:2 caddy hash-password
   ```
   Paste the resulting `$2a$...` hash into the appended site block (see
   `Caddyfile.snippet.example`) in place of the placeholder, and pick your
   own username in place of `seller`.
5. **Append the site block** from `Caddyfile.snippet.example` to the
   existing shared Caddyfile, with your real domain, then reload that Caddy
   instance (e.g. `docker compose exec caddy caddy reload --config
   /etc/caddy/Caddyfile` from wherever the shared stack lives).
6. **Clone this repo** on the server at the path you'll use for
   `DEPLOY_PATH` (below), and copy your real `.env` there (never commit it —
   see `.env.example` for the required keys, plus `EBAY_REDIRECT_URI` must be
   updated to `https://<your-domain>/api/auth/ebay/callback` and registered
   as an accepted redirect URI on your eBay developer application).
7. **Bring the stack up once manually** to confirm it works before wiring
   CI:
   ```bash
   docker compose up -d --build
   ```
8. **Create a dedicated, low-privilege `deploy` user** whose SSH key can run
   *only* the deploy command, so a leaked GitHub secret can't be used for
   anything else (skip this if you already made one for the tourism
   generator and are happy reusing it — just point its forced command at
   this repo's path instead, or add a second `authorized_keys` line with a
   different forced command for this path):
   ```bash
   sudo useradd --create-home --shell /usr/sbin/nologin deploy
   sudo -u deploy mkdir -p /home/deploy/.ssh
   ```
   Generate a dedicated key pair for CI (on your own machine, not the
   server): `ssh-keygen -t ed25519 -f deploy_key -C "github-actions-deploy"`.
   Then, as root on the server, add the **public** half to
   `/home/deploy/.ssh/authorized_keys` with a forced command so the key can
   never be used interactively:
   ```text
   command="cd /path/to/ebay-listing-copilot && git pull --ff-only && docker compose up -d --build --remove-orphans",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAA...
   ```
   ```bash
   sudo chown -R deploy:deploy /home/deploy/.ssh
   sudo chmod 700 /home/deploy/.ssh
   sudo chmod 600 /home/deploy/.ssh/authorized_keys
   ```
9. **Register the GitHub secrets** (from your own machine, with `gh`
   authenticated as the repo owner):
   ```bash
   gh secret set DEPLOY_SSH_KEY < deploy_key
   gh secret set DEPLOY_HOST -b "your.server.ip.or.hostname"
   gh secret set DEPLOY_USER -b "deploy"
   gh secret set DEPLOY_PATH -b "/path/to/ebay-listing-copilot"
   gh secret set DEPLOY_HEALTHCHECK_URL -b "https://<your-domain>/api/health"
   ```
   Then delete the local `deploy_key` private key file — only the GitHub
   secret and the server's `authorized_keys` need to keep it.
10. Optionally, protect the `production` GitHub Environment (used by
    `deploy.yml`) with required reviewers, so a push can't auto-deploy
    without a human clicking approve.

After that, every push to `master` touching the paths listed in
`deploy.yml` redeploys automatically. The recurring deploy never touches
your own laptop or network — GitHub's cloud runners SSH directly to the
server; only this one-time bootstrap needs a trusted device.

## Data persistence

`backend/data/` is bind-mounted (not a Docker volume), so `docker compose
down` never deletes it and it's a plain directory you can back up with
`rsync`/`tar`. It holds the SQLite database and uploaded photo originals —
treat backups of it with the same care as the credentials in `.env` (see
[`docs/privacy.md`](privacy.md) for what's actually in there).
