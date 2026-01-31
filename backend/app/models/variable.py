from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import ForeignKey, String, Float, Integer, Boolean, DateTime, Enum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db_base import Base


class VariableType(str, PyEnum):
    """Typ zmiennej - określa kategorię zmiennej w systemie."""
    PHYSICAL_CONSTANT = "physical_constant"
    ENGINEERING_PROCESS_METRIC = "engineering_process_metric"
    BUSINESS_KPI = "business_kpi"
    SUBJECTIVE_FACTOR = "subjective_factor"


class VariableSource(str, PyEnum):
    """Źródło pochodzenia danych zmiennej."""
    HARD_DATA = "hard_data"
    USER_INPUT = "user_input"
    AI_SUGGESTION = "ai_suggestion"
    MIXED = "mixed"


class Variable(Base):
    """
    Model reprezentujący zmienną w systemie Product Optimizer.
    
    Zmienna może reprezentować stałą fizyczną, metrykę procesu inżynierskiego,
    wskaźnik biznesowy (KPI) lub czynnik subiektywny.
    """
    __tablename__ = "variables"

    # Podstawowe pola
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Typ zmiennej (enum jako native PostgreSQL enum)
    variable_type: Mapped[VariableType] = mapped_column(
        Enum(VariableType, name="variable_type_enum", create_type=True),
        nullable=False,
        default=VariableType.ENGINEERING_PROCESS_METRIC
    )

    # Domain constraints
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Provenance (pochodzenie danych)
    source: Mapped[VariableSource] = mapped_column(
        Enum(VariableSource, name="variable_source_enum", create_type=True),
        nullable=False,
        default=VariableSource.USER_INPUT
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0
    )
    source_description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Layer info (hierarchia zmiennych)
    layer_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_variable_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("variables.id", ondelete="SET NULL"),
        nullable=True
    )

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

    # Self-referential relationship dla hierarchii
    parent: Mapped[Optional["Variable"]] = relationship(
        "Variable",
        remote_side="Variable.id",
        back_populates="children"
    )
    children: Mapped[list["Variable"]] = relationship(
        "Variable",
        back_populates="parent"
    )

    # Relationships dla powiązań (jako źródło lub cel)
    outgoing_relationships: Mapped[list["Relationship"]] = relationship(
        "Relationship",
        foreign_keys="Relationship.source_variable_id",
        back_populates="source_variable"
    )
    incoming_relationships: Mapped[list["Relationship"]] = relationship(
        "Relationship",
        foreign_keys="Relationship.target_variable_id",
        back_populates="target_variable"
    )

    # Table constraints
    __table_args__ = (
        # Walidacja: min_value < max_value (jeśli oba są ustawione)
        CheckConstraint(
            "(min_value IS NULL OR max_value IS NULL OR min_value < max_value)",
            name="check_min_max_values"
        ),
        # Walidacja: confidence w zakresie 0-1
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="check_confidence_range"
        ),
        # Walidacja: layer_level >= 0
        CheckConstraint(
            "layer_level >= 0",
            name="check_layer_level_positive"
        ),
    )

    def __repr__(self) -> str:
        return f"<Variable(id={self.id}, name='{self.name}', type={self.variable_type.value})>"
