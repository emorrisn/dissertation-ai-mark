from api.extensions import db
from api.models.user import User
from api.models.user_update import UserUpdate


def seed_updates():

    users = User.query.all()

    if not users:
        print("No users found. Seed users first.")
        return

    updates = []

    for user in users:

        # Prevent reseeding duplicates
        exists = UserUpdate.query.filter_by(user_id=user.id).first()
        if exists:
            continue

        updates.extend([
            UserUpdate(
                user_id=user.id,
                type="NewFeature",
                title="Welcome to the system",
                message="Thank you for using our system!",
            ),
            UserUpdate(
                user_id=user.id,
                type="SystemMessage",
                title="Feedback",
                message="Please give as much feedback as you can!"
            )
        ])

    if updates:
        db.session.add_all(updates)
        db.session.commit()
        print(f"{len(updates)} updates seeded.")
    else:
        print("Updates already seeded.")