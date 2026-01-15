# Tests Manuels

Ce répertoire contient des tests manuels et scripts de diagnostic qui ne font pas partie de la suite de tests automatisés.

---

## 📁 Fichiers

### test_func_now_bug.py

**But:** Démontrer le bug de l'utilisation de `func.now()` en Python.

**Problème démontré:**
- `func.now()` est une expression SQLAlchemy qui ne s'évalue qu'en SQL
- Quand assigné directement à un attribut Python, il ne renvoie pas une datetime
- Cela cause des erreurs de sérialisation JSON et des comparaisons incorrectes

**Utilisation:**
```bash
python tests/manual/test_func_now_bug.py
```

**Résultat attendu:**
- ❌ Test 1 montre que `func.now()` ne fonctionne pas en Python
- ✅ Test 2 montre que `datetime.now(timezone.utc)` fonctionne correctement

**Fix appliqué:** Tous les usages de `func.now()` ont été remplacés par `datetime.now(timezone.utc)` dans le codebase.

---

### test_refactoring.py

**But:** Vérifier la refactorisation du schema `product_attributes`.

**Ce qu'il teste:**
1. Vérifie que le schema `product_attributes` existe
2. Vérifie que les tables sont dans le bon schema
3. Vérifie que les modèles Python fonctionnent
4. Vérifie que les catégories sont accessibles
5. Vérifie que les Foreign Keys sont correctes

**Utilisation:**
```bash
python tests/manual/test_refactoring.py
```

**Note:** Ce test est spécifique à une migration historique et peut ne plus être pertinent si le schema a évolué.

---

## ⚠️ Important

Ces tests ne sont **PAS** exécutés automatiquement par `pytest`. Ils sont conservés pour:
- Documentation historique
- Diagnostic manuel
- Reproduction de bugs

Pour les tests automatisés, voir:
- `tests/unit/` - Tests unitaires
- `tests/integration/` - Tests d'intégration

---

**Dernière mise à jour:** 2025-12-08
