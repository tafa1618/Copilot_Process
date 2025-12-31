# preprocessing/llti_preprocess.py

import pandas as pd
from datetime import datetime


def preprocess_llti(df_bo: pd.DataFrame) -> pd.DataFrame:
    """
    Prépare le dataset LLTI (Lead Time Facturation Service)
    - Trimestre en cours
    - Facture par facture
    - Matériels Caterpillar uniquement
    - Dossiers avec pointage
    """

    df = df_bo.copy()

    # ==================================================
    # COLONNES NÉCESSAIRES
    # ==================================================
    required_cols = [
        "N° OR (Segment)",
        "N° Facture (Lignes)",
        "Date Facture (Lignes)",
        "Pointage dernière date (Segment)",
        "Nom Client OR (or)",
        "Numéro série Equipement (Segment)",
        "Constructeur de l'équipement",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans BO : {missing}")

    df = df[required_cols]

    # ==================================================
    # TYPAGE DATES
    # ==================================================
    df["Date Facture (Lignes)"] = pd.to_datetime(
        df["Date Facture (Lignes)"], errors="coerce"
    )
    df["Pointage dernière date (Segment)"] = pd.to_datetime(
        df["Pointage dernière date (Segment)"], errors="coerce"
    )

    # ==================================================
    # FILTRE : MATÉRIELS CATERPILLAR UNIQUEMENT
    # ==================================================
    df = df[
        df["Constructeur de l'équipement"]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("CATERPILLAR")
    ]

    # ==================================================
    # FILTRE : FACTURES AVEC POINTAGE
    # ==================================================
    df = df[
        df["Pointage dernière date (Segment)"].notna()
        & df["Date Facture (Lignes)"].notna()
    ]

    # ==================================================
    # FILTRE : TRIMESTRE EN COURS
    # ==================================================
    today = pd.Timestamp.today().normalize()
    trimestre_debut = today.to_period("Q").start_time

    df = df[df["Date Facture (Lignes)"] >= trimestre_debut]

    # ==================================================
    # DÉDUPLICATION FACTURE PAR FACTURE
    # ==================================================
    df = (
        df.sort_values("Pointage dernière date (Segment)")
        .drop_duplicates(subset=["N° Facture (Lignes)"], keep="last")
    )

    # ==================================================
    # CALCUL LLTI (jours)
    # ==================================================
    df["LLTI_jours"] = (
        df["Date Facture (Lignes)"]
        - df["Pointage dernière date (Segment)"]
    ).dt.days

    # ==================================================
    # NETTOYAGE FINAL
    # ==================================================
    df = df[df["LLTI_jours"] >= 0]

    return df.reset_index(drop=True)
