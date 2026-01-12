# preprocessing/llti_preprocessing.py

import pandas as pd
from datetime import datetime


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

    df["Date Facture (Lignes)"] = pd.to_datetime(
        df["Date Facture (Lignes)"], errors="coerce"
    )

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
    df["Date Facture (Lignes)"] = pd.to_datetime(df["Date Facture (Lignes)"], errors="coerce")
    df["Pointage dernière date (Segment)"] = pd.to_datetime(df["Pointage dernière date (Segment)"], errors="coerce")

    # Supprimer lignes sans dates valides ou sans numéro de facture
    df = df.dropna(subset=["Date Facture (Lignes)", "Pointage dernière date (Segment)", "N° Facture (Lignes)"])

    return df
