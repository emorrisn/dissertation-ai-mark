import uuid
from datetime import datetime
from api.extensions import db
from sqlalchemy import event
import os
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
    
@event.listens_for(SessionFile, 'after_delete')
def delete_file_from_disk(mapper, connection, target):
    """
    Listen for the 'after_delete' event on SessionFile.
    When a record is deleted from the DB, delete the actual file from the filesystem.
    """
    if target.storage_url:
        # Assuming target.storage_url is a relative path like 'uploads/markschemes/...'
        # We convert it to an absolute path to be safe.
        file_path = os.path.join(os.getcwd(), target.storage_url)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Successfully deleted physical file: {file_path}")
            except OSError as e:
                # Log the error, but don't crash the DB transaction since it's an after_delete hook
                print(f"Error deleting file {file_path}: {e}")