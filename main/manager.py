# Flask-Script (previously used here) is abandoned and incompatible with the
# Click version bundled in modern Flask, so it's been removed. Flask-Migrate
# provides its own CLI commands directly via Flask's own `flask` command —
# no manager.py needed for that anymore. This file just registers the
# migration extension so `flask db ...` works if you want to manage schema
# changes with Alembic instead of relying on `db.create_all()`:
#
#   docker compose exec main env FLASK_APP=manager.py flask db init
#   docker compose exec main env FLASK_APP=manager.py flask db migrate -m "..."
#   docker compose exec main env FLASK_APP=manager.py flask db upgrade

from main import app, db
from flask_migrate import Migrate

migrate = Migrate(app, db)
