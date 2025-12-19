"""
Plugin Task Model

Taches en attente d'execution par le plugin browser.

Business Rules (Updated: 2025-12-12):
- Architecture step-by-step synchrone (comme pythonApiWOO)
- Chaque task = UNE requete HTTP simple (POST /api/v2/photos, etc.)
- Le plugin poll GET /api/plugin/tasks toutes les 5s
- Le plugin execute http_method + path uniquement
- Le backend orchestre avec await wait_for_task_completion()
- Pas de TaskType - le backend garde le contexte via async/await

Author: Claude
Date: 2025-12-12
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class TaskStatus(str, Enum):
    """Status d'une tache."""
    PENDING = "pending"      # En attente d'execution par le plugin
    PROCESSING = "processing"  # En cours d'execution
    SUCCESS = "success"      # Executee avec succes
    FAILED = "failed"        # Echec d'execution
    TIMEOUT = "timeout"      # Expire (> 1h)
    CANCELLED = "cancelled"  # Annulee par l'utilisateur


class PluginTask(Base):
    """
    Tache a executer par le plugin browser.

    Table tenant-specific (client_{id}.plugin_tasks).
    Architecture simplifiée : chaque tache = 1 requête HTTP simple.
    Le backend orchestre step-by-step avec await.
    """
    __tablename__ = "plugin_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Task type (optionnel, pour legacy/debugging uniquement)
    task_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Type legacy (optionnel) - non utilisé par le plugin"
    )

    # Status
    # Note: values_callable fait que SQLEnum stocke "success" au lieu de "SUCCESS"
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(
            TaskStatus,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True
    )

    # Payload JSON (donnees pour executer la tache)
    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Donnees pour executer la tache (product_id, title, price, etc.)"
    )

    # Result JSON (retour du plugin apres execution)
    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Resultat retourne par le plugin (vinted_id, url, error, etc.)"
    )

    # Error message
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relations optionnelles
    product_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Job reference (for job orchestration system)
    job_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("vinted_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent job for this task"
    )

    # Informations de la requête HTTP
    platform: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Plateforme cible (vinted, ebay, etsy)"
    )

    http_method: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Méthode HTTP (POST, PUT, DELETE, GET)"
    )

    path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Path API complet (ex: /api/v2/photos)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Quand le plugin a commence l'execution"
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Quand la tache a ete terminee (succes ou echec)"
    )

    # Retry
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Nombre de tentatives d'execution"
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False
    )

    # Relationship to job
    job = relationship("VintedJob", back_populates="tasks", lazy="select")

    def __repr__(self) -> str:
        method = self.http_method or "?"
        path_preview = (self.path[:30] + "...") if self.path and len(self.path) > 30 else (self.path or "?")
        return f"<PluginTask(id={self.id}, {method} {path_preview}, status={self.status})>"
