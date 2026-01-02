# preprocessing/productivite_preprocessing.py

import pandas as pd


def preprocess_productivite(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Préprocessing générique productivité
    - Typage
    - Colonnes standard
    - Nettoyage données incohérentes
    """

    df = df_raw.copy()

    # ===============================
    # COLONNES REQUISES
    # ===============================
    required_cols = [
        "Saisie heures - Date",
        "Salarié - Nom",
        "Salarié - Equipe(Nom)",
        "Facturable",
        "Hr_Totale",
        "Hr_Théorique",
        "Service"
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    # ===============================
    # TYPAGE
    # ===============================
    df["Saisie heures - Date"] = pd.to_datetime(
        df["Saisie heures - Date"], errors="coerce"
    )

    numeric_cols = [
        "Facturable",
        "Hr_Totale",
        "Hr_Théorique"
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # ===============================
    # FILTRES MÉTIER DE BASE
    # ===============================
    df = df[df["Saisie heures - Date"].notna()]
    df = df[df["Salarié - Nom"].notna()]

    # ===============================
    # FEATURES TEMPORELLES
    # ===============================
    df["Jour"] = df["Saisie heures - Date"].dt.day
    df["Jour_semaine"] = df["Saisie heures - Date"].dt.weekday
    df["Mois"] = df["Saisie heures - Date"].dt.to_period("M").astype(str)

    # ===============================
    # PRODUCTIVITÉ JOUR
    # ===============================
    df["Productivite_jour"] = df.apply(
        lambda r: r["Facturable"] / r["Hr_Totale"]
        if r["Hr_Totale"] > 0 else 0,
        axis=1
    )

    return df.reset_index(drop=True)
