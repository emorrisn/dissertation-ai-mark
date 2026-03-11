from api.seeders.seed_users import seed_users
from api.seeders.seed_updates import seed_updates


def seed_all():
    seed_users()
    seed_updates()

    print("Database seeded successfully")