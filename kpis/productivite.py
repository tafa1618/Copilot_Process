# kpis/productivite.py

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from preprocessing.preprocess_productivite import preprocess_productivite
from preprocessing.exhaustivite_preprocessing import compute_exhaustivite



def preprocess_productivite(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Préprocessing Productivité : Nettoyage et Agrégation par Jour/Technicien.
    """
    df = df_raw.copy()

    # 1. Normalisation des noms de colonnes (supprime les espaces inutiles en début/fin)
    df.columns = df.columns.str.strip()

    # 2. Définition des colonnes requises (Sync avec le dashboard)
    # Les noms doivent correspondre EXACTEMENT à ton fichier Excel
    COL_DATE = "Saisie heures - Date"
    COL_NOM = "Salarié - Nom"
    COL_EQUIPE = "Salarié - Equipe(Nom)"
    COL_FACT = "Facturable"
    COL_TRAV = "Hr_travaillée"
    COL_TOT = "Hr_Totale"
    COL_THEO = "Hr_Théorique"
    COL_JOUR_SEM = "Jour_semaine"

    required_cols = [COL_DATE, COL_NOM, COL_EQUIPE, COL_FACT, COL_TRAV, COL_TOT, COL_THEO, COL_JOUR_SEM]

    # Vérification de présence
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Colonnes manquantes dans le fichier : {missing}")
        st.info(f"Colonnes détectées : {df.columns.tolist()}")
        return pd.DataFrame()

    # 3. Typage et Nettoyage
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")
    
    numeric_cols = [COL_FACT, COL_TRAV, COL_TOT, COL_THEO]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df.dropna(subset=[COL_DATE, COL_NOM])

    # 4. Agrégation (On groupe par jour et par technicien)
    # On garde les colonnes descriptives dans le groupby
    df_day = (
        df.groupby(
            [COL_DATE, COL_NOM, COL_EQUIPE, COL_JOUR_SEM, COL_THEO, COL_TOT],
            as_index=False
        )
        .agg({
            COL_TRAV: "sum",
            COL_FACT: "sum"
        })
    )

    # 5. Features Temporelles
    df_day["Mois"] = df_day[COL_DATE].dt.to_period("M").astype(str)

    return df_day.reset_index(drop=True)
