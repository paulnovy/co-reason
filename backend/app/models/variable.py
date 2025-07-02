from sqlalchemy import Column, Integer, String, Float

from ..database import Base


class Variable(Base):
    __tablename__ = "variables"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    min = Column(Float, nullable=False)
    max = Column(Float, nullable=False)
