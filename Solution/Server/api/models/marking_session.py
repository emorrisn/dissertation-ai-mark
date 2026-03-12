from api.extensions import db
from datetime import datetime
import uuid


class MarkingSession(db.Model):
    __tablename__ = "marking_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    year = db.Column(db.Integer, nullable=False)
    students_amount = db.Column(db.Integer, default=1)
    selected_student = db.Column(db.Integer, default=1)

    required_outputs = db.Column(db.JSON, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    status = db.Column(
        db.String(20),
        default="pending"
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    ended_at = db.Column(db.DateTime, nullable=True)

    markschemes = db.relationship(
        "MarkScheme",
        backref="session",
        lazy=True,
        cascade="all, delete-orphan"
    )

    student_submissions = db.relationship(
        "StudentSubmission",
        backref="session",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "year": self.year,
            "studentsAmount": self.students_amount,
            "selectedStudent": self.selected_student,
            "requiredOutputs": self.required_outputs or [],
            "notes": self.notes or "",
            "status": self.status,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }