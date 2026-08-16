from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def create_tenant(db: Session, data: dict) -> Tenant:
    tenant = Tenant(**data)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def get_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def get_tenants(db: Session) -> List[Tenant]:
    return db.query(Tenant).all()


def update_tenant(db: Session, tenant_id: int, data: dict) -> Optional[Tenant]:
    tenant = get_tenant(db, tenant_id)
    if not tenant:
        return None

    for field, value in data.items():
        setattr(tenant, field, value)

    db.commit()
    db.refresh(tenant)
    return tenant


def delete_tenant(db: Session, tenant_id: int) -> bool:
    tenant = get_tenant(db, tenant_id)
    if not tenant:
        return False

    db.delete(tenant)
    db.commit()
    return True
