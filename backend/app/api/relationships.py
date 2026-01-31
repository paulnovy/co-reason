from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

from ..models.relationship import Relationship, RelationshipType, RelationshipDirection, RelationshipShape
from ..models.variable import Variable
from ..deps import get_db


# ============== Pydantic Schemas ==============

class RelationshipBase(BaseModel):
    """Bazowy model dla Relationship."""
    source_variable_id: int = Field(..., gt=0, description="ID zmiennej źródłowej")
    target_variable_id: int = Field(..., gt=0, description="ID zmiennej docelowej")
    relationship_type: RelationshipType = Field(
        default=RelationshipType.INFLUENCES,
        description="Typ relacji"
    )
    direction: RelationshipDirection = Field(
        default=RelationshipDirection.UNKNOWN,
        description="Kierunek relacji"
    )
    shape: RelationshipShape = Field(
        default=RelationshipShape.UNKNOWN,
        description="Kształt relacji"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Pewność relacji (0-1)"
    )
    provenance_source: Optional[str] = Field(None, max_length=500, description="Źródło pochodzenia")
    description: Optional[str] = Field(None, max_length=1000, description="Opis relacji")

    @field_validator('target_variable_id')
    @classmethod
    def validate_not_self_reference(cls, v: int, info) -> int:
        """Walidacja: source i target nie mogą być takie same."""
        source_id = info.data.get('source_variable_id')
        if source_id is not None and v == source_id:
            raise ValueError('source_variable_id and target_variable_id cannot be the same')
        return v


class RelationshipCreate(RelationshipBase):
    """Model do tworzenia nowej relacji."""
    pass


class RelationshipUpdate(BaseModel):
    """Model do aktualizacji relacji (wszystkie pola opcjonalne)."""
    relationship_type: Optional[RelationshipType] = None
    direction: Optional[RelationshipDirection] = None
    shape: Optional[RelationshipShape] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    provenance_source: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class RelationshipRead(RelationshipBase):
    """Model do odczytu relacji (zawiera wszystkie pola)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RelationshipDetailRead(RelationshipRead):
    """Model do odczytu relacji ze szczegółami zmiennych."""
    source_variable_name: Optional[str] = None
    target_variable_name: Optional[str] = None


class RelationshipList(BaseModel):
    """Model listy relacji z paginacją."""
    items: List[RelationshipRead]
    total: int
    skip: int
    limit: int


class RelationshipFilter(BaseModel):
    """Model filtrowania relacji."""
    source_variable_id: Optional[int] = None
    target_variable_id: Optional[int] = None
    relationship_type: Optional[RelationshipType] = None
    direction: Optional[RelationshipDirection] = None


# ============== Router ==============

router = APIRouter(prefix="/relationships", tags=["relationships"])


# ============== Helper Functions ==============

def check_variable_exists(db: Session, variable_id: int, active_only: bool = True) -> bool:
    """Sprawdza czy zmienna istnieje."""
    query = db.query(Variable).filter(Variable.id == variable_id)
    if active_only:
        query = query.filter(Variable.is_active == True)
    return query.first() is not None


# ============== CRUD Endpoints ==============

@router.post("", response_model=RelationshipRead, status_code=status.HTTP_201_CREATED)
def create_relationship(rel: RelationshipCreate, db: Session = Depends(get_db)):
    """
    Tworzy nową relację między zmiennymi.
    
    - Sprawdza istnienie obu zmiennych
    - Zapobiega duplikatom (ta sama para source->target)
    - Waliduje self-reference
    """
    # Sprawdź czy zmienne istnieją
    if not check_variable_exists(db, rel.source_variable_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source variable with id {rel.source_variable_id} not found"
        )
    
    if not check_variable_exists(db, rel.target_variable_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target variable with id {rel.target_variable_id} not found"
        )
    
    # Sprawdź czy relacja już istnieje (zapobieganie duplikatom)
    existing = db.query(Relationship).filter(
        Relationship.source_variable_id == rel.source_variable_id,
        Relationship.target_variable_id == rel.target_variable_id,
        Relationship.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Relationship from variable {rel.source_variable_id} to {rel.target_variable_id} already exists"
        )
    
    # Utwórz relację
    db_rel = Relationship(**rel.model_dump())
    db.add(db_rel)
    db.commit()
    db.refresh(db_rel)
    return db_rel


@router.get("", response_model=RelationshipList)
def list_relationships(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    include_inactive: bool = Query(False, description="Include soft-deleted relationships"),
    source_variable_id: Optional[int] = Query(None, description="Filter by source variable ID"),
    target_variable_id: Optional[int] = Query(None, description="Filter by target variable ID"),
    relationship_type: Optional[RelationshipType] = Query(None, description="Filter by relationship type"),
    direction: Optional[RelationshipDirection] = Query(None, description="Filter by direction"),
    shape: Optional[RelationshipShape] = Query(None, description="Filter by shape"),
    db: Session = Depends(get_db)
):
    """
    Lista relacji z opcjonalnym filtrowaniem i paginacją.
    """
    query = db.query(Relationship)
    
    # Filtrowanie
    if not include_inactive:
        query = query.filter(Relationship.is_active == True)
    if source_variable_id is not None:
        query = query.filter(Relationship.source_variable_id == source_variable_id)
    if target_variable_id is not None:
        query = query.filter(Relationship.target_variable_id == target_variable_id)
    if relationship_type:
        query = query.filter(Relationship.relationship_type == relationship_type)
    if direction:
        query = query.filter(Relationship.direction == direction)
    if shape:
        query = query.filter(Relationship.shape == shape)
    
    # Liczba wszystkich rekordów
    total = query.count()
    
    # Pobierz dane z paginacją
    items = query.offset(skip).limit(limit).all()
    
    return RelationshipList(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{relationship_id}", response_model=RelationshipDetailRead)
def get_relationship(
    relationship_id: int,
    include_inactive: bool = Query(False, description="Include soft-deleted relationship"),
    db: Session = Depends(get_db)
):
    """
    Pobiera pojedynczą relację po ID ze szczegółami zmiennych.
    """
    query = db.query(Relationship).filter(Relationship.id == relationship_id)
    
    if not include_inactive:
        query = query.filter(Relationship.is_active == True)
    
    db_rel = query.first()
    
    if not db_rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship with id {relationship_id} not found"
        )
    
    # Pobierz nazwy zmiennych dla szczegółów
    source_var = db.query(Variable).filter(Variable.id == db_rel.source_variable_id).first()
    target_var = db.query(Variable).filter(Variable.id == db_rel.target_variable_id).first()
    
    # Utwórz odpowiedź z szczegółami
    result = RelationshipDetailRead.model_validate(db_rel)
    result.source_variable_name = source_var.name if source_var else None
    result.target_variable_name = target_var.name if target_var else None
    
    return result


@router.patch("/{relationship_id}", response_model=RelationshipRead)
def update_relationship(
    relationship_id: int,
    rel_update: RelationshipUpdate,
    db: Session = Depends(get_db)
):
    """
    Aktualizuje relację (częściowa aktualizacja - PATCH).
    """
    # Pobierz relację
    db_rel = db.query(Relationship).filter(
        Relationship.id == relationship_id,
        Relationship.is_active == True
    ).first()
    
    if not db_rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship with id {relationship_id} not found"
        )
    
    # Aktualizuj pola
    update_data = rel_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rel, field, value)
    
    db.commit()
    db.refresh(db_rel)
    return db_rel


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relationship(
    relationship_id: int,
    hard_delete: bool = Query(False, description="Permanently delete instead of soft delete"),
    db: Session = Depends(get_db)
):
    """
    Usuwa relację (soft delete lub hard delete).
    
    Soft delete ustawia is_active=False.
    Hard delete całkowicie usuwa rekord z bazy.
    """
    db_rel = db.query(Relationship).filter(Relationship.id == relationship_id).first()
    
    if not db_rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship with id {relationship_id} not found"
        )
    
    if hard_delete:
        db.delete(db_rel)
    else:
        db_rel.is_active = False
    
    db.commit()
    return None


@router.post("/{relationship_id}/restore", response_model=RelationshipRead)
def restore_relationship(
    relationship_id: int,
    db: Session = Depends(get_db)
):
    """
    Przywraca usuniętą relację (soft restore).
    """
    db_rel = db.query(Relationship).filter(
        Relationship.id == relationship_id,
        Relationship.is_active == False
    ).first()
    
    if not db_rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deleted relationship with id {relationship_id} not found"
        )
    
    db_rel.is_active = True
    db.commit()
    db.refresh(db_rel)
    return db_rel


# ============== Additional Endpoints ==============

@router.get("/variable/{variable_id}/outgoing", response_model=List[RelationshipRead])
def get_outgoing_relationships(
    variable_id: int,
    include_inactive: bool = Query(False, description="Include soft-deleted relationships"),
    db: Session = Depends(get_db)
):
    """
    Pobiera wszystkie relacji wychodzące z danej zmiennej.
    """
    # Sprawdź czy zmienna istnieje
    if not check_variable_exists(db, variable_id, active_only=not include_inactive):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variable with id {variable_id} not found"
        )
    
    query = db.query(Relationship).filter(
        Relationship.source_variable_id == variable_id
    )
    
    if not include_inactive:
        query = query.filter(Relationship.is_active == True)
    
    return query.all()


@router.get("/variable/{variable_id}/incoming", response_model=List[RelationshipRead])
def get_incoming_relationships(
    variable_id: int,
    include_inactive: bool = Query(False, description="Include soft-deleted relationships"),
    db: Session = Depends(get_db)
):
    """
    Pobiera wszystkie relacji przychodzące do danej zmiennej.
    """
    # Sprawdź czy zmienna istnieje
    if not check_variable_exists(db, variable_id, active_only=not include_inactive):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variable with id {variable_id} not found"
        )
    
    query = db.query(Relationship).filter(
        Relationship.target_variable_id == variable_id
    )
    
    if not include_inactive:
        query = query.filter(Relationship.is_active == True)
    
    return query.all()


@router.get("/variable/{variable_id}/all", response_model=List[RelationshipRead])
def get_all_variable_relationships(
    variable_id: int,
    include_inactive: bool = Query(False, description="Include soft-deleted relationships"),
    db: Session = Depends(get_db)
):
    """
    Pobiera wszystkie relacji (wychodzące i przychodzące) dla danej zmiennej.
    """
    # Sprawdź czy zmienna istnieje
    if not check_variable_exists(db, variable_id, active_only=not include_inactive):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variable with id {variable_id} not found"
        )
    
    query = db.query(Relationship).filter(
        (Relationship.source_variable_id == variable_id) |
        (Relationship.target_variable_id == variable_id)
    )
    
    if not include_inactive:
        query = query.filter(Relationship.is_active == True)
    
    return query.all()
