from api.seeders.seed_all import seed_all
from api.seeders.seed_users import seed_users
from api.seeders.seed_updates import seed_updates


import click
from flask.cli import with_appcontext

@click.command("seed")
@click.argument("model", required=False)
@with_appcontext
def seed(model):
    """Seed the database."""

    seeders = {
        "users": seed_users,
        "updates": seed_updates,
    }

    if model:
        seeder = seeders.get(model)

        if not seeder:
            click.echo(f"Unknown seeder: {model}")
            click.echo(f"Available seeders: {', '.join(seeders.keys())}")
            return

        click.echo(f"Seeding {model}...")
        seeder()
        click.echo(f"{model} seeded.")
    else:
        click.echo("Seeding all models...")
        seed_all()
        click.echo("Database seeded.")