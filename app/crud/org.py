from sqlalchemy.orm import Session
from datetime import datetime

from app.models.org import Organization
from app.models.tenant import Tenant
from app.models.enterprise import EnterpriseSettings


class OrgCRUD:

    # ---------------------------------------------------------
    # Create Organization
    # ---------------------------------------------------------
    def create_org(self, db: Session, data: dict):
        org = Organization(
            name=data["name"],
            industry=data.get("industry"),
            country=data.get("country"),
            timezone=data.get("timezone"),
            contact_email=data.get("contact_email"),
            contact_phone=data.get("contact_phone"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(org)
        db.commit()
        db.refresh(org)

        # create default enterprise settings
        settings = EnterpriseSettings(
            organization_id=org.id,
            compliance_rules="{}",
            forecasting_model="prophet",
            ai_mode="balanced",
            dashboard_config="{}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(settings)
        db.commit()

        return org

    # ---------------------------------------------------------
    # Get Organization
    # ---------------------------------------------------------
    def get_org(self, db: Session, org_id: int):
        return db.query(Organization).filter(Organization.id == org_id).first()

    # ---------------------------------------------------------
    # List Organizations
    # ---------------------------------------------------------
    def list_orgs(self, db: Session):
        return db.query(Organization).filter(Organization.is_active == True).all()

    # ---------------------------------------------------------
    # Update Organization
    # ---------------------------------------------------------
    def update_org(self, db: Session, org_id: int, updates: dict):
        org = self.get_org(db, org_id)
        if not org:
            raise ValueError("Organization not found.")

        for key, value in updates.items():
            if hasattr(org, key):
                setattr(org, key, value)

        org.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(org)
        return org

    # ---------------------------------------------------------
    # Deactivate Organization
    # ---------------------------------------------------------
    def deactivate_org(self, db: Session, org_id: int):
        org = self.get_org(db, org_id)
        if not org:
            raise ValueError("Organization not found.")

        org.is_active = False
        org.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(org)
        return org

    # ---------------------------------------------------------
    # Create Tenant
    # ---------------------------------------------------------
    def create_tenant(self, db: Session, org_id: int, name: str, description: str = None):
        tenant = Tenant(
            organization_id=org_id,
            name=name,
            description=description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    # ---------------------------------------------------------
    # List Tenants
    # ---------------------------------------------------------
    def list_tenants(self, db: Session, org_id: int):
        return db.query(Tenant).filter(
            Tenant.organization_id == org_id,
            Tenant.is_active == True
        ).all()

    # ---------------------------------------------------------
    # Update Enterprise Settings
    # ---------------------------------------------------------
    def update_settings(self, db: Session, org_id: int, updates: dict):
        settings = db.query(EnterpriseSettings).filter(
            EnterpriseSettings.organization_id == org_id
        ).first()

        if not settings:
            raise ValueError("Enterprise settings not found.")

        for key, value in updates.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        settings.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(settings)
        return settings
