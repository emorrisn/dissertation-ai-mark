import uuid
from datetime import datetime
from api.extensions import db


class SessionFile(db.Model):
    __tablename__ = "session_files"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(1024), nullable=False)
    storage_url = db.Column(db.String(1024), nullable=False)

    size = db.Column(db.Integer)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "storageUrl": self.storage_url,
            "size": self.size,
            "uploadedAt": self.uploaded_at.isoformat(),
            "deletedAt": self.deleted_at.isoformat() if self.deleted_at else None
        }