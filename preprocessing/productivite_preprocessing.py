"""Shim de compatibilité restauré.

Ce module existe uniquement pour compatibilité ascendante avec d'anciens imports
comme `from preprocessing.productivite_preprocessing import preprocess_produc`.
Il émet un avertissement de dépréciation pour encourager la migration vers
`preprocessing.preprocess_productivite.preprocess_productivite`.
"""

from __future__ import annotations

import warnings
from .preprocess_productivite import preprocess_productivite

warnings.warn(
    "preprocessing.productivite_preprocessing is deprecated — import from preprocessing.preprocess_productivite instead",
    DeprecationWarning,
)

# Alias historique attendu par certains déploiements
preprocess_produc = preprocess_productivite

__all__ = ["preprocess_productivite", "preprocess_produc"]
