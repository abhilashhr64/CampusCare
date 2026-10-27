import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.modules.tenancy.models import College


class CollegeResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    domain: str
    is_active: bool
    settings: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class CollegeCreate(BaseModel):
    name: str
    code: str
    domain: str
    settings: Optional[Dict[str, Any]] = None


class TenancyService:
    @staticmethod
    def get_all_active_colleges(db: Session) -> List[College]:
        stmt = select(College).where(College.is_active == True).order_by(College.name)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_college_by_id(db: Session, college_id: uuid.UUID) -> Optional[College]:
        return db.get(College, college_id)

    @staticmethod
    def get_college_by_domain(db: Session, domain: str) -> Optional[College]:
        stmt = select(College).where(College.domain == domain, College.is_active == True)
        return db.scalar(stmt)

    @staticmethod
    def create_college(db: Session, data: CollegeCreate) -> College:
        college = College(
            name=data.name,
            code=data.code,
            domain=data.domain,
            settings=data.settings or {},
            is_active=True,
        )
        db.add(college)
        db.commit()
        db.refresh(college)
        return college
