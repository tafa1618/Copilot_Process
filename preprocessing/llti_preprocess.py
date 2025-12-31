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
# 4️⃣ SÉLECTION COLONNES LLTI
# ======================================================
def select_llti_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "N° OR (Segment)",
        "N° Facture (Lignes)",
        "Date Facture (Lignes)",
        "Pointage dernière date (Segment)",
        "Nom Client OR (or)",
        "Numéro série Equipement (Segment)",
    ]

    return df[columns].copy()


# ======================================================
# 5️⃣ PIPELINE COMPLET LLTI
# ======================================================
def preprocess_llti(file) -> pd.DataFrame:
    """
    Pipeline LLTI :
    BO → Trimestre courant → OR pointés → Facture par facture
    """
    df = load_bo_file(file)
    df = filter_current_quarter(df)
    df = filter_or_with_pointage(df)
    df = select_llti_columns(df)

    # Nettoyage final
    df = df.dropna(subset=["N° Facture (Lignes)"])

    return df
