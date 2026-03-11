import uuid
from api.extensions import db
from datetime import datetime

class StudentSubmission(db.Model):
    __tablename__ = "student_submissions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    session_id = db.Column(db.String(36), db.ForeignKey("marking_sessions.id"), nullable=False)

    student_no = db.Column(db.Integer)

    contents = db.Column(db.Text)

    pages = db.relationship("SubmissionPage", backref="submission", cascade="all, delete-orphan")
    feedback = db.relationship("MarkingFeedback", backref="submission", cascade="all, delete-orphan")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sessionId": self.session_id,
            "studentNo": self.student_no,
            "pages": [p.to_dict() for p in self.pages],
            "contents": self.contents,
            "feedback": [f.to_dict() for f in self.feedback],
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat()
        }