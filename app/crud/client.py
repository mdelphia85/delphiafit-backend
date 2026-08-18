from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.client import Client


def create_client(db: Session, data: dict) -> Client:
    client = Client(**data)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def get_client(db: Session, client_id: int) -> Optional[Client]:
    return db.query(Client).filter(Client.id == client_id).first()


def get_clients(db: Session) -> List[Client]:
    return db.query(Client).all()


def update_client(db: Session, client_id: int, data: dict) -> Optional[Client]:
    client = get_client(db, client_id)
    if not client:
        return None

    for field, value in data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client_id: int) -> bool:
    client = get_client(db, client_id)
    if not client:
        return False

    db.delete(client)
    db.commit()
    return True
