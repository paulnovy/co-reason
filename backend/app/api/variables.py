from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

from ..models.variable import Variable, VariableType, VariableSource
from ..deps import get_db


# ============== Pydantic Schemas ==============

class VariableBase(BaseModel):
    """Bazowy model dla Variable."""
    name: str = Field(..., min_length=1, max_length=255, description="Nazwa zmiennej")
    description: Optional[str] = Field(None, max_length=1000, description="Opis zmiennej")
    symbol: Optional[str] = Field(None, max_length=50, description="Symbol zmiennej (opcjonalny)")
    variable_type: VariableType = Field(
        default=VariableType.ENGINEERING_PROCESS_METRIC,
        description="Typ zmiennej"
    )
    min_value: Optional[float] = Field(None, description="Minimalna wartość (opcjonalna)")
    max_value: Optional[float] = Field(None, description="Maksymalna wartość (opcjonalna)")
    unit: Optional[str] = Field(None, max_length=50, description="Jednostka miary (opcjonalna)")
    source: VariableSource = Field(
        default=VariableSource.USER_INPUT,
        description="Źródło pochodzenia danych"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Pewność danych (0-1)"
    )
    source_description: Optional[str] = Field(None, max_length=1000, description="Opis źródła")
    layer_level: int = Field(default=0, ge=0, description="Poziom warstwy w hierarchii")
    parent_variable_id: Optional[int] = Field(None, description="ID zmiennej nadrzędnej")

    @field_validator('max_value')
    @classmethod
    def validate_max_value(cls, v: Optional[float], info) -> Optional[float]:
        """Walidacja: max_value musi być większe niż min_value."""
        if v is not None:
            min_val = info.data.get('min_value')
            if min_val is not None and v <= min_val:
                raise ValueError('max_value must be greater than min_value')
        return v


class VariableCreate(VariableBase):
    """Model do tworzenia nowej zmiennej."""
    pass


class VariableUpdate(BaseModel):
    """Model do aktualizacji zmiennej (wszystkie pola opcjonalne)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    symbol: Optional[str] = Field(None, max_length=50)
    variable_type: Optional[VariableType] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)
    source: Optional[VariableSource] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    source_description: Optional[str] = Field(None, max_length=1000)
    layer_level: Optional[int] = Field(None, ge=0)
    parent_variable_id: Optional[int] = None
    is_active: Optional[bool] = None


class VariableRead(VariableBase):
    """Model do odczytu zmiennej (zawiera wszystkie pola)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VariableList(BaseModel):
    """Model listy zmiennych z paginacją."""
    items: List[VariableRead]
    total: int
    skip: int
    limit: int


# ============== Router ==============

router = APIRouter(prefix="/variables", tags=["variables"])


# ============== CRUD Endpoints ==============

@router.post("", response_model=VariableRead, status_code=status.HTTP_201_CREATED)
def create_variable(var: VariableCreate, db: Session = Depends(get_db)):
    """
    Tworzy nową zmienną.
    
    - Sprawdza unikalność nazwy
    - Waliduje constraint min < max
    - Obsługuje hierarchię (parent_variable_id)
    """
    # Sprawdź czy nazwa już istnieje
    existing = db.query(Variable).filter(Variable.name == var.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Variable with name '{var.name}' already exists"
        )
    
    # Sprawdź czy parent_variable_id istnieje (jeśli podane)
    if var.parent_variable_id is not None:
        parent = db.query(Variable).filter(
            Variable.id == var.parent_variable_id,
            Variable.is_active == True
        ).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent variable with id {var.parent_variable_id} not found"
            )
    
    # Utwórz nową zmienną
    db_var = Variable(**var.model_dump())
    db.add(db_var)
    db.commit()
    db.refresh(db_var)
    return db_var


@router.get("", response_model=VariableList)
def list_variables(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    include_inactive: bool = Query(False, description="Include soft-deleted variables"),
    variable_type: Optional[VariableType] = Query(None, description="Filter by variable type"),
    layer_level: Optional[int] = Query(None, ge=0, description="Filter by layer level"),
    parent_id: Optional[int] = Query(None, description="Filter by parent variable ID"),
    db: Session = Depends(get_db)
):
    """
    Lista zmiennych z opcjonalnym filtrowaniem i paginacją.
    """
    query = db.query(Variable)
    
    # Filtrowanie
    if not include_inactive:
        query = query.filter(Variable.is_active == True)
    if variable_type:
        query = query.filter(Variable.variable_type == variable_type)
    if layer_level is not None:
        query = query.filter(Variable.layer_level == layer_level)
    if parent_id is not None:
        query = query.filter(Variable.parent_variable_id == parent_id)
    
    # Liczba wszystkich rekordów (dla paginacji)
    total = query.count()
    
    # Pobierz dane z paginacją
    items = query.offset(skip).limit(limit).all()
    
    return VariableList(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{variable_id}", response_model=VariableRead)
def get_variable(
    variable_id: int,
    include_inactive: bool = Query(False, description="Include soft-deleted variable"),
    db: Session = Depends(get_db)
):
    """
    Pobiera pojedynczą zmienną po ID.
    """
    query = db.query(Variable).filter(Variable.id == variable_id)
    
    if not include_inactive:
        query = query.filter(Variable.is_active == True)
    
    db_var = query.first()
    
    if not db_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variable with id {variable_id} not found"
        )
    
    return db_var


@router.patch("/{variable_id}", response_model=VariableRead)
def update_variable(
    variable_id: int,
    var_update: VariableUpdate,
    db: Session = Depends(get_db)
):
    """
    Aktualizuje zmienną (częściowa aktualizacja - PATCH).
    
    - Sprawdza unikalność nazwy (jeśli zmieniana)
    - Waliduje constraint min < max
    - Obsługuje zmianę rodzica
    """
    # Pobierz zmienną
    db_var = db.query(Variable).filter(
        Variable.id == variable_id,
        Variable.is_active == True
    ).first()
    
    if not db_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variable with id {variable_id} not found"
        )
    
    # Sprawdź unikalność nazwy (jeśli zmieniana)
    if var_update.name is not None and var_update.name != db_var.name:
        existing = db.query(Variable).filter(Variable.name == var_update.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Variable with name '{var_update.name}' already exists"
            )
    
    # Sprawdź czy parent_variable_id istnieje (jeśli podane)
    if var_update.parent_variable_id is not None:
        # Zapobiegaj cyklowi (nie można być własnym przodkiem)
        if var_update.parent_variable_id == variable_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Variable cannot be its own parent"
            )
        
        parent = db.query(Variable).filter(
            Variable.id == var_update.parent_variable_id,
            Variable.is_active == True
        ).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent variable with id {var_update.parent_variable_id} not found"
            )
    
    # Walidacja min/max
    new_min = var_update.min_value if var_update.min_value is not None else db_var.min_value
    new_max = var_update.max_value if var_update.max_value is not None else db_var.max_value
    
    if new_min is not None and new_max is not None and new_max <= new_min:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="max_value must be greater than min_value"
        )
    
    # Aktualizuj pola
    update_data = var_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_var, field, value)
    
    db.commit()
    db.refresh(db_var)
    return db_var


@router.delete("/{variable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variable(
    variable_id: int,
    hard_delete: bool = Query(False, description="Permanently delete instead of soft delete"),
    db: Session = Depends(get_db)
):
    """
    Usuwa zmienną (soft delete lub hard delete).
    
    Soft delete ustawia is_active=False.
    Hard delete całkowicie usuwa rekord z bazy.
    """
    db_var = db.query(Variable).filter(Variable.id == variable_id).first()
    
    if not db_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variable with id {variable_id} not found"
        )
    
    if hard_delete:
        db.delete(db_var)
    else:
        db_var.is_active = False
    
    db.commit()
    return None


@router.post("/{variable_id}/restore", response_model=VariableRead)
def restore_variable(
    variable_id: int,
    db: Session = Depends(get_db)
):
    """
    Przywraca usuniętą zmienną (soft restore).
    """
    db_var = db.query(Variable).filter(
        Variable.id == variable_id,
        Variable.is_active == False
    ).first()
    
    if not db_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deleted variable with id {variable_id} not found"
        )
    
    db_var.is_active = True
    db.commit()
    db.refresh(db_var)
    return db_var


@router.get("/{variable_id}/children", response_model=List[VariableRead])
def get_variable_children(
    variable_id: int,
    db: Session = Depends(get_db)
):
    """
    Pobiera wszystkie bezpośrednie dzieci zmiennej (zmienne podrzędne).
    """
    # Sprawdź czy zmienna istnieje
    db_var = db.query(Variable).filter(
        Variable.id == variable_id,
        Variable.is_active == True
    ).first()
    
    if not db_var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variable with id {variable_id} not found"
        )
    
    children = db.query(Variable).filter(
        Variable.parent_variable_id == variable_id,
        Variable.is_active == True
    ).all()
    
    return children
