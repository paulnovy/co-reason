from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import ForeignKey, String, Float, Integer, Boolean, DateTime, Enum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db_base import Base


class RelationshipType(str, PyEnum):
    """Typ relacji między zmiennymi."""
    DRIVES = "drives"  # Jedna zmienna bezpośrednio napędza drugą
    INFLUENCES = "influences"  # Jedna zmienna wpływa na drugą
    CORRELATES_WITH = "correlates_with"  # Korelacja bez kierunku przyczynowego


class RelationshipDirection(str, PyEnum):
    """Kierunek relacji (dodatni/ujemny)."""
    POSITIVE = "positive"  # Wzrost A → wzrost B
    NEGATIVE = "negative"  # Wzrost A → spadek B
    UNKNOWN = "unknown"  # Nieznany kierunek


class RelationshipShape(str, PyEnum):
    """Kształt relacji (charakter zależności)."""
    LINEAR = "linear"  # Liniowa zależność
    NONLINEAR = "nonlinear"  # Nieliniowa zależność
    THRESHOLD = "threshold"  # Efekt progowy
    UNKNOWN = "unknown"  # Nieznany kształt


class Relationship(Base):
    """
    Model reprezentujący relację między dwiema zmiennymi.
    
    Relacja opisuje jak jedna zmienna wpływa na drugą,
    wraz z metadanymi o charakterze tego wpływu.
    """
    __tablename__ = "relationships"

    # Podstawowe pola
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Powiązania ze zmiennymi
    source_variable_id: Mapped[int] = mapped_column(
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    target_variable_id: Mapped[int] = mapped_column(
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Typ relacji
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, name="relationship_type_enum", create_type=True),
        nullable=False,
        default=RelationshipType.INFLUENCES
    )

    # Kierunek relacji
    direction: Mapped[RelationshipDirection] = mapped_column(
        Enum(RelationshipDirection, name="relationship_direction_enum", create_type=True),
        nullable=False,
        default=RelationshipDirection.UNKNOWN
    )

    # Kształt relacji
    shape: Mapped[RelationshipShape] = mapped_column(
        Enum(RelationshipShape, name="relationship_shape_enum", create_type=True),
        nullable=False,
        default=RelationshipShape.UNKNOWN
    )

    # Confidence (pewność relacji) 0-1
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5
    )

    # Źródło pochodzenia relacji
    provenance_source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Dodatkowy opis relacji
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Soft delete flag
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships do zmiennych
    source_variable: Mapped["Variable"] = relationship(
        "Variable",
        foreign_keys=[source_variable_id],
        back_populates="outgoing_relationships"
    )
    target_variable: Mapped["Variable"] = relationship(
        "Variable",
        foreign_keys=[target_variable_id],
        back_populates="incoming_relationships"
    )

    # Table constraints
    __table_args__ = (
        # Walidacja: source != target (nie można mieć relacji ze sobą)
        CheckConstraint(
            "source_variable_id != target_variable_id",
            name="check_no_self_reference"
        ),
        # Walidacja: confidence w zakresie 0-1
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="check_rel_confidence_range"
        ),
        # Unikalność: jedna relacja danego typu między tymi samymi zmiennymi
        # (zapobiega duplikatom)
    )

    def __repr__(self) -> str:
        return (
            f"<Relationship(id={self.id}, "
            f"source={self.source_variable_id} -> target={self.target_variable_id}, "
            f"type={self.relationship_type.value})>"
        )
