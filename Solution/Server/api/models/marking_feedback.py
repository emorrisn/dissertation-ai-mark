import uuid
from api.extensions import db
from datetime import datetime

class MarkingFeedback(db.Model):
    __tablename__ = "marking_feedback"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    submission_id = db.Column(db.String(36), db.ForeignKey("student_submissions.id"))

    student_no = db.Column(db.Integer)

    type = db.Column(db.String(100))

    teacher_comments = db.Column(db.Text)

    is_selected = db.Column(db.Boolean, default=False)

    confidence = db.Column(db.Float)

    description = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "studentNo": self.student_no,
            "type": self.type,
            "teacherComments": self.teacher_comments,
            "isSelected": self.is_selected,
            "confidence": self.confidence,
            "description": self.description,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat()
        }