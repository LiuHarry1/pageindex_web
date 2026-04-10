from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, DateTime, func

from ..database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_path = Column(String(512), nullable=False)
    index_path = Column(String(512), nullable=True)
    status = Column(String(20), default="uploading", nullable=False)
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    doc_name = Column(String(255), nullable=True)
    doc_description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "status": self.status,
            "error_message": self.error_message,
            "page_count": self.page_count,
            "doc_name": self.doc_name,
            "doc_description": self.doc_description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
