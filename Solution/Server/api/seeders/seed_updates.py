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
                type="MarkingSessionUpdate",
                title="Marking Complete",
                message="Your marking session 'History Essay Batch 1' has been completed.",
                link="/dashboard/marking/session-123",
                related_id="session-123"
            ),
            UserUpdate(
                user_id=user.id,
                type="NewFeature",
                title="New Feature: Bulk Export",
                message="You can now export marking results as a CSV file.",
                link="/dashboard/features"
            ),
            UserUpdate(
                user_id=user.id,
                type="SystemMessage",
                title="Scheduled Maintenance",
                message="The system will be down for maintenance on Sunday at 2 AM."
            )
        ])

    if updates:
        db.session.add_all(updates)
        db.session.commit()
        print(f"{len(updates)} updates seeded.")
    else:
        print("Updates already seeded.")