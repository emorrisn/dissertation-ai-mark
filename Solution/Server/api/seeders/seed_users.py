from api.extensions import db
from api.models.user import User


def seed_users():

    users = [
        {
            "username": "teacher1",
            "name": "Alice Smith",
            "email": "alice.teacher@mail.com",
            "institute_code": "oxford",
            "writing_style": ["Balanced", "Technical"],
            "password": "password123"
        },
        {
            "username": "teacher2",
            "name": "Bob Johnson",
            "email": "bob.johnson@mail.com",
            "institute_code": "cambridge",
            "writing_style": ["Strict"],
            "password": "password123"
        }
    ]

    for u in users:

        exists = User.query.filter_by(
            username=u["username"],
            institute_code=u["institute_code"]
        ).first()

        if exists:
            continue

        user = User(
            username=u["username"],
            name=u["name"],
            email=u["email"],
            institute_code=u["institute_code"]
        )

        user.set_password(u["password"])

        db.session.add(user)

    db.session.commit()
    print("Users seeded")