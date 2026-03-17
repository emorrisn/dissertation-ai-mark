import uuid
from api.extensions import db
from datetime import datetime

class MarkingFeedback(db.Model):
    __tablename__ = "marking_feedback"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = db.Column(db.String(36), db.ForeignKey("student_submissions.id"))
    student_no = db.Column(db.Integer)

    description = db.Column(db.Text)  # Short description of the feedback overall
    teacher_comments = db.Column(db.Text)
    is_selected = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One-to-Many Relationship: Links the 3 overall feedbacks to their specific output chunks
    items = db.relationship("MarkingFeedbackItem", backref="feedback", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "submissionId": self.submission_id,
            "studentNo": self.student_no,
            "description": self.description,
            "teacherComments": self.teacher_comments,
            "isSelected": self.is_selected,
            "confidence": self.confidence,
            "items": [item.to_dict() for item in self.items],
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat()
        }