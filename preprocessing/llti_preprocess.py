# preprocessing/llti_preprocessing.py

import pandas as pd
from datetime import datetime
from typing import Optional


def _parse_date_series(s: pd.Series, prefer_dayfirst: Optional[bool] = None) -> pd.Series:
    """Parse une Series de dates en testant dayfirst=True et dayfirst=False et
    en retenant la conversion la plus complète.

    Si `prefer_dayfirst` est True/False, on force cette reconstruction.
    """
    if s is None:
        return s
    if hasattr(s, 'dtype') and (str(s.dtype).startswith('datetime') or s.dtype == 'datetime64[ns]'):
        return s
    try:
        parsed_df = pd.to_datetime(s, errors='coerce', dayfirst=True)
    except TypeError:
        parsed_df = pd.to_datetime(s, errors='coerce')
    parsed_en = pd.to_datetime(s, errors='coerce', dayfirst=False)

    if prefer_dayfirst is True:
        return parsed_df
    if prefer_dayfirst is False:
        return parsed_en

    if parsed_df.notna().sum() >= parsed_en.notna().sum():
        return parsed_df
    return parsed_en


# ======================================================
# 1️⃣ CHARGEMENT
# ======================================================
def load_bo_file(file) -> pd.DataFrame:
    """
    Accepte chemin local ou UploadFile / buffer
    """
    if isinstance(file, str):
        return pd.read_excel(file)
    return pd.read_excel(file)


# ======================================================
# 2️⃣ FILTRE TRIMESTRE COURANT
# ======================================================
def filter_current_quarter(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Les dates dans les fichiers BO sont en format français (jour/mois/année)
    df["Date Facture (Lignes)"] = _parse_date_series(df["Date Facture (Lignes)"], prefer_dayfirst=True)

    today = datetime.today()
    current_quarter = (today.month - 1) // 3 + 1
    current_year = today.year

    df = df[
        (df["Date Facture (Lignes)"].dt.year == current_year)
        & (df["Date Facture (Lignes)"].dt.quarter == current_quarter)
    ]

    return df


# ======================================================
# 3️⃣ FILTRE OR AVEC POINTAGE
# ======================================================
def filter_or_with_pointage(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = df[
        df["Pointage dernière date (Segment)"].notna()
    ]

    return df


# ======================================================
# 4️⃣ FILTRAGE PAR CONSTRUCTEUR + SÉLECTION COLONNES LLTI
# ======================================================

def filter_caterpillar(df: pd.DataFrame) -> pd.DataFrame:
    """Garde uniquement les lignes où le constructeur est Caterpillar (insensible à la casse)."""
    df = df.copy()
    col = "Constructeur de l'équipement"
    if col not in df.columns:
        return df

    df[col] = df[col].astype(str).str.strip()
    df = df[df[col].str.lower() == "caterpillar"]
    return df


def select_llti_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "N° OR (Segment)",
        "N° Facture (Lignes)",
        "Date Facture (Lignes)",
        "Pointage dernière date (Segment)",
        "Nom Client OR (or)",
        "Numéro série Equipement (Segment)",
        "Constructeur de l'équipement",
    ]

    # Sélection sécurisée : éviter KeyError explicite
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes pour LLTI: {missing}")

    return df[columns].copy()


# ======================================================
# 5️⃣ PIPELINE COMPLET LLTI
# ======================================================

def preprocess_llti(file) -> pd.DataFrame:
    """
    Pipeline LLTI :
    BO → Filtre constructeur Caterpillar → Trimestre courant → OR pointés → Sélection colonnes
    """
    df = load_bo_file(file)

    # Validation colonnes clés avant traitement
    required_cols = [
        "N° OR (Segment)",
        "Pointage dernière date (Segment)",
        "Date Facture (Lignes)",
        "Constructeur de l'équipement",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes pour LLTI: {missing}")

    # Nettoyages et filtres
    df = filter_caterpillar(df)
    df = filter_current_quarter(df)
    df = filter_or_with_pointage(df)
    df = select_llti_columns(df)

    # Assurer les types dates
    df["Date Facture (Lignes)"] = _parse_date_series(df["Date Facture (Lignes)"], prefer_dayfirst=True)
    df["Pointage dernière date (Segment)"] = _parse_date_series(df["Pointage dernière date (Segment)"], prefer_dayfirst=True)

    # Supprimer lignes sans dates valides ou sans numéro de facture
    df = df.dropna(subset=["Date Facture (Lignes)", "Pointage dernière date (Segment)", "N° Facture (Lignes)"])

    return df
