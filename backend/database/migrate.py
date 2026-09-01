"""Run the additive GIDS mobile PostgreSQL migration once.

Usage from the backend directory:
    python -m database.migrate

Run this after Railway PostgreSQL has been added and DATABASE_URL is visible
inside the backend service. It is idempotent and safe to run again.
"""

from database.connection import run_mobile_migration


if __name__ == "__main__":
    run_mobile_migration()
    print("GIDS mobile database migration completed successfully.")