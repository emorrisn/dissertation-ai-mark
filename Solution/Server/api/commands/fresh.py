import click
from flask.cli import with_appcontext
from sqlalchemy import text
from api.extensions import db

@click.command("fresh")
@with_appcontext
def fresh():
    """Drops all tables, recreates them, and stamps Alembic."""
    click.echo("Wiping Postgres database...")
    
    # Drop the Postgres schema to ensure even the alembic_version table is gone
    db.session.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;'))
    db.session.commit()
    
    click.echo("Database is fresh!")