# Running polyglot-commerce with Docker

This project already had a `docker-compose.yml` and Dockerfiles, but the
compose file was missing a service the app actually depends on, several
files were pointed at infrastructure that no longer exists, and a couple of
packages were pinned to versions that don't work together. Everything below
reflects what's fixed. See "What was found and fixed" for the full list.

## 1. Run it

```bash
docker compose up -d --build
```

No `.env` file is required. First build takes a while — two separate Python
dependency installs, a Django/Flask stack each, and a full CRA production
build for the frontend.

```bash
docker compose logs -f
```

Then open:

- **`http://localhost:3000`** — the public storefront (`main` service, port 8001)
- **`http://localhost:3000/admin/products`** — the admin CRUD panel (`admin` service, port 8000)
- **`http://localhost:15672`** — RabbitMQ's management UI (guest/guest)

## 2. Sample data

3 sample products are seeded automatically — no manual step required:

- **admin's database** gets them via a Django data migration
  (`admin/products/migrations/0002_seed_products.py`), which runs
  automatically as part of the `python manage.py migrate` step already in
  the `admin` service's startup command.
- **main's database** gets the same 3 products (same IDs, so both sides
  agree) directly in `main.py`'s startup code, guarded so it only seeds
  once and only when the table is empty.

They're seeded into both databases independently, rather than relying on
the RabbitMQ event round-trip, because that round-trip has an inherent
startup-ordering race (see "Known limitations" below) that isn't worth
depending on just to get the initial seed to show up reliably.

A single `User` row is also seeded (admin's database) — see "What was found
and fixed" for why.

## 3. What was found and fixed

### The app pointed at infrastructure that no longer exists

- **`main.py`**, and all four React components (`Products.tsx`,
  `ProductsCreate.tsx`, `ProductsEdit.tsx`, `Main.tsx`), had a hardcoded
  external IP (`http://34.170.196.139:8000` / `:8001`) baked in — almost
  certainly the original developer's now-defunct cloud VM. The app could
  only ever have worked there. Replaced with `ADMIN_SERVICE_URL` (backend,
  defaults to `http://admin:8000` — the Docker service name) and
  `REACT_APP_ADMIN_API_URL` / `REACT_APP_MAIN_API_URL` (frontend, baked in
  at build time via `docker-compose.yml`'s build args).
- **All four RabbitMQ producer/consumer files** (`main/producer.py`,
  `main/consumer.py`, `admin/consumer.py`, `admin/products/producer.py`)
  had a live-looking CloudAMQP connection string with real-looking
  credentials hardcoded in — meaning the whole event-driven side of the app
  depended on a specific third party's cloud account, which **docker-compose
  never even had a RabbitMQ service for**. The `queue-main`/`queue-admin`
  containers would have crashed on startup. Added a `rabbitmq` service and
  pointed all four files at it via `RABBITMQ_URL` (defaults to
  `amqp://guest:guest@rabbitmq:5672/%2F`).
- If you had a real CloudAMQP account tied to those old credentials,
  consider rotating it — those credentials were sitting in this repo.

### Real bugs, not just wiring

- **`main`-service's `Product` model had no `likes` column at all**, even
  though the storefront UI renders `{p.likes} likes` on every card — it
  would always have shown `undefined` (and `NaN` after clicking Like, since
  the frontend does `p.likes++` locally). Added the column and now
  increment it directly when a like is recorded, instead of only tracking
  likes in the admin database.
- **`ProductsEdit.tsx` used `defaultValue`** on the title/image inputs.
  `defaultValue` only applies at mount — since the product fetch resolves
  *after* mount, the edit form always rendered blank fields regardless of
  the product's actual data. Changed to a properly controlled `value`.
- **Publishers never declared their queue before publishing.** RabbitMQ
  silently drops a message published to a queue that doesn't exist yet; if
  a consumer hadn't started and declared its queue first, an early message
  (like the very first product create on a fresh boot) could vanish. Both
  producers now declare their queue too, which is idempotent and safe.
- **`UserAPIView`'s `random.choice(User.objects.all())`** would raise
  `IndexError` on an empty table — and nothing seeded any `User` rows or
  even exposed the model in Django admin. Registered `Product`/`User` in
  `admin.py` and seeded one `User` row alongside the sample products, so
  the storefront's "Like" button doesn't 500 on a fresh install.

### Outdated / broken package versions

| Package | Was | Now | Why |
|---|---|---|---|
| MySQL (both DBs) | `5.7.22` | `8.4` | 5.7 reached end-of-life Oct 2023 |
| Node (frontend build) | `16-alpine` | `22-alpine` | 16 is EOL; 22 is current Active LTS |
| Python (both services) | `3.9-slim` | `3.12-slim` | 3.9 is nearing end of security support |
| Django | `3.1.3` | `4.2.16` | **This is Django's actual official LTS release**, supported through April 2026 |
| Flask | `1.1.2` | `3.0.3` | 1.1.2 + itsdangerous 2.x (also pinned) is a **known-broken combination** — this pairing likely didn't even run |
| Flask-Script | `2.0.6` | *removed* | Abandoned since ~2016, incompatible with the Click version modern Flask bundles. `flask db migrate/upgrade` (via Flask-Migrate) replaces it — see `main/manager.py` |
| React | `16.14.0` | `18.3.1` | 16 no longer receives updates |
| react-router-dom | `5.2.0` | `6.26.2` | v5 is unmaintained; migrated `Redirect`→`Navigate`, `props.match.params`→`useParams`, route syntax |
| react-scripts (CRA) | `3.4.3` | `5.0.1` | last CRA release; 3.x has known issues on modern Node |
| TypeScript | `3.7.5` | `4.9.5` | kept on the 4.x line deliberately — it's the version react-scripts 5's own template ships with, avoiding dependency-resolution fights that TS5 can cause with CRA 5 |
| SQLAlchemy / Flask-SQLAlchemy | `1.3.20` / `2.4.4` | `2.0.35` / `3.1.1` | current stable |
| Everything else (`requests`, `mysqlclient`, `pika`, `Flask-Cors`, `django-cors-headers`, DRF, etc.) | various | current stable | — |

The frontend build was validated for real in this environment (`npm run
build` completes cleanly, zero TypeScript errors from the React 18/router
v6 migration). The Python side could not be `pip install`-verified the same
way here, so double-check `docker compose logs -f admin main` on first boot.

### Two settings.py fixes that come with the Django 4.2 bump

- `CORS_ORIGIN_ALLOW_ALL` (old django-cors-headers setting name, renamed
  years ago) → `CORS_ALLOW_ALL_ORIGINS`.
- Removed `USE_L10N = True` — deprecated since Django 4.0, always `True`
  now regardless of the setting.
- Added `DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'` explicitly.
  Modern Django defaults new auto PKs to `BigAutoField` and warns if you
  don't set this; setting it to the original `AutoField` avoids a spurious
  migration wanting to widen the `id` column, since the compose file runs
  `makemigrations` on every container start.

## 4. Known limitations

- **RabbitMQ startup ordering isn't fully deterministic on a cold start.**
  `queue-main`/`queue-admin` wait for their own service (`main`/`admin`) to
  report healthy, but the *other* side's consumer isn't guaranteed to be up
  yet the first time a real product create/update/delete happens
  immediately after `docker compose up`. In practice RabbitMQ queues
  messages once declared, and both producers now declare their queue
  before publishing, so this mostly self-heals within a few seconds — but
  it's why the initial 3-product seed is done directly in both databases
  rather than relying on this path.
- **The "Like" feature's user identity is a stand-in.** `GET /api/user`
  just returns a random row from an essentially empty `User` table — this
  was already how the app worked before these fixes; not something this
  pass was meant to redesign.
- **`DEBUG = True` and `ALLOWED_HOSTS = ['*']`** in Django settings, and
  Flask's `debug=True` — both fine for local use, not something you'd want
  facing the public internet as-is.
- A few `href="#"` accessibility lint warnings remain in placeholder nav
  links (`Nav.tsx`, `Menu.tsx`, the delete action in `Products.tsx`) —
  cosmetic, left alone since fixing them means changing those elements to
  buttons, which is a bigger change than "update outdated packages."
