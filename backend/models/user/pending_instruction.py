"""
Model pour tracker les instructions en attente d'exécution par le frontend.

Ce modèle remplace le système de polling PluginTask pour les opérations synchrones.
Il permet au backend d'orchestrer les actions du plugin en créant des instructions
que le frontend récupère et exécute.

Author: Claude
Date: 2026-01-06
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from shared.database import UserBase


class PendingInstruction(UserBase):
    """
    Instructions en attente d'exécution par le frontend.

    Workflow:
    1. Backend crée une instruction (status=pending)
    2. Frontend récupère l'instruction
    3. Frontend exécute l'action via le plugin
    4. Frontend envoie le résultat au backend
    5. Backend met à jour l'instruction (status=completed/failed)

    Attributes:
        id: UUID unique de l'instruction
        user_id: ID de l'utilisateur propriétaire
        action: Type d'action (check_vinted_connection, sync_products, etc.)
        status: État de l'instruction (pending, completed, failed, expired)
        result: Résultat de l'exécution (JSONB)
        error: Message d'erreur en cas d'échec
        created_at: Date de création
        completed_at: Date de complétion
        expires_at: Date d'expiration (auto-cleanup)
    """
    __tablename__ = "pending_instructions"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, nullable=False, index=True)
    action = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_pending_instructions_user_status', 'user_id', 'status'),
        {"schema": "tenant"},  # Placeholder for schema_translate_map
    )

    def __repr__(self):
        return f"<PendingInstruction(id={self.id}, action={self.action}, status={self.status})>"
