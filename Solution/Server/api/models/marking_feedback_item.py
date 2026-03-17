import uuid
from api.extensions import db
from datetime import datetime

class MarkingFeedbackItem(db.Model):
    __tablename__ = "marking_feedback_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Links back to the parent MarkingFeedback
    feedback_id = db.Column(db.String(36), db.ForeignKey("marking_feedback.id", ondelete="CASCADE"))
    
    # e.g., "Give Feedback", "Score Work", "Section by Section"
    type = db.Column(db.String(100)) 
    
    # The actual AI generated text for this specific output requirement
    contents = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "contents": self.contents,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat()
        }