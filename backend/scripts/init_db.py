"""
Script d'initialisation de la base de données (version simplifiée sans tenant).

Ce script crée toutes les tables nécessaires dans le schema public.
"""

import sys
from pathlib import Path

# Ajouter le projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.database import engine, Base

# Import all models pour que SQLAlchemy les connaisse
from models.public.user import User, SubscriptionTier
from models.public.brand import Brand
from models.public.category import Category
from models.public.color import Color
from models.public.condition import Condition
from models.public.fit import Fit
from models.public.gender import Gender
from models.public.material import Material
from models.public.season import Season
from models.public.size import Size

def init_db():
    """Crée toutes les tables dans la base de données."""
    print("🔧 Création des tables...")

    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)

    print("✅ Tables créées avec succès dans le schema 'public'!")
    print("\nTables créées:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

if __name__ == "__main__":
    init_db()
