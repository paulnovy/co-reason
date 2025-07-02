from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..models.variable import Variable
from ..deps import get_db


class VariableCreate(BaseModel):
    name: str
    min: float
    max: float


class VariableRead(BaseModel):
    id: int
    name: str
    min: float
    max: float

    class Config:
        orm_mode = True


router = APIRouter()


@router.post("/variables", response_model=VariableRead, status_code=status.HTTP_201_CREATED)
def create_variable(var: VariableCreate, db: Session = Depends(get_db)):
    if var.min >= var.max:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="min must be less than max")
    existing = db.query(Variable).filter(Variable.name == var.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="name already exists")
    db_var = Variable(name=var.name, min=var.min, max=var.max)
    db.add(db_var)
    db.commit()
    db.refresh(db_var)
    return db_var


@router.get("/variables", response_model=list[VariableRead])
def list_variables(db: Session = Depends(get_db)):
    return db.query(Variable).all()
