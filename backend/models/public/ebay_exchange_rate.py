"""
Modèle pour les taux de change EUR → autres devises.

Stocke les taux de conversion pour GBP et PLN (les seules devises non-EUR).
Mis à jour mensuellement via API ECB (European Central Bank).

Author: Claude
Date: 2025-12-10
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, func
from shared.database import Base


class ExchangeRate(Base):
    """Taux de change EUR vers autres devises"""

    __tablename__ = 'exchange_rate_config'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    currency = Column(String(3), unique=True, nullable=False, index=True, comment="GBP, PLN")
    rate = Column(Numeric(10, 6), nullable=False, comment="Ex: 0.856234 (1 EUR = 0.856234 GBP)")
    source = Column(String(50), default='ECB', nullable=False, comment="Source du taux (ECB, manual, fallback)")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def convert(self, amount_eur: float) -> float:
        """
        Convertit un montant EUR vers cette devise.

        Args:
            amount_eur: Montant en EUR

        Returns:
            float: Montant converti dans la devise

        Examples:
            >>> # Pour GBP avec rate = 0.85
            >>> rate = ExchangeRate(currency='GBP', rate=0.85)
            >>> rate.convert(100.00)
            85.00
        """
        return float(amount_eur) * float(self.rate)

    def __repr__(self):
        return f"<ExchangeRate(currency='{self.currency}', rate={self.rate}, updated={self.updated_at})>"
