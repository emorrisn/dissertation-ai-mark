import uuid
from api.extensions import db
from datetime import datetime

class SubmissionPage(db.Model):
    __tablename__ = "submission_pages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    submission_id = db.Column(db.String(36), db.ForeignKey("student_submissions.id"))

    page_no = db.Column(db.Integer)

    file_id = db.Column(db.String(36), db.ForeignKey("session_files.id"))
    file = db.relationship("SessionFile")

    def to_dict(self):
        return {
            "pageNo": self.page_no,
            "file": self.file.to_dict() if self.file else None
        }