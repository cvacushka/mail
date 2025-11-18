from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Attachment(Base):
    __tablename__ = "attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    attachment_type = Column(String(50), nullable=False)  # 'item', 'currency', 'gold', etc.
    item_id = Column(Integer, nullable=True)  # ID игрового предмета
    item_name = Column(String(200), nullable=True)  # Название предмета
    quantity = Column(Numeric(10, 2), default=1.0)  # Количество
    attachment_data = Column(JSON, nullable=True)  # JSON с дополнительными данными
    
    # Relationships
    message = relationship("Message", back_populates="attachments")
    
    def __repr__(self):
        return f"<Attachment(id={self.id}, type={self.attachment_type}, quantity={self.quantity})>"

