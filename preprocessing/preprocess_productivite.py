# preprocessing/productivite_preprocessing.py

import pandas as pd


def preprocess_productivite(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Préprocessing Productivité
    - Agrégation JOUR / TECHNICIEN
    - Exploite Jour_semaine & Hr_Théorique existants
    - Produit un DF canonique (1 ligne = 1 tech / 1 jour)
    """

    df = df_raw.copy()
    st.write("Colonnes détectées :")
    for c in df.columns:
        st.write(f"'{c}'")


    # ==================================================
    # COLONNES MINIMALES REQUISES
    # ==================================================
    required_cols = [
        "Saisie heures - Date",
        "Salarié - Nom",
        "Salarié-Equipe(Nom)",
        "Facturable",
        "Hr_travaillée",
        "Hr_Totale",
        "Hr_Théorique",
        "Jour_semaine"
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    # ==================================================
    # TYPAGE
    # ==================================================
    df["Saisie heures - Date"] = pd.to_datetime(
        df["Saisie heures - Date"], errors="coerce"
    )

    for col in ["Facturable", "Hr_travaillée", "Hr_Totale", "Hr_Théorique"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df[df["Saisie heures - Date"].notna()]
    df = df[df["Salarié - Nom"].notna()]

    # ==================================================
    # AGRÉGATION MÉTIER (LE POINT CLÉ)
    # ==================================================
    # 👉 plusieurs lignes possibles par jour / technicien
    df_day = (
        df
        .groupby(
            [
                "Saisie heures - Date",
                "Salarié - Nom",
                "Salarié - Equipe(Nom)",
                "Jour_semaine",
                "Hr_Théorique"
                "Hr_Totale"
            ],
            as_index=False
        )
        .agg(
            {
                "Hr_Travaillée": "sum",
                "Facturable": "sum"
            }
        )
    )

    # ==================================================
    # FEATURES TEMPORELLES
    # ==================================================
    df_day["Jour"] = df_day["Saisie heures - Date"].dt.day
    df_day["Mois"] = df_day["Saisie heures - Date"].dt.to_period("M").astype(str)

    # ==================================================
    # PRODUCTIVITÉ JOUR
    # ==================================================
    df_day["Productivite_jour"] = df_day.apply(
        lambda r: r["Facturable"] / r["Hr_travaillée"]
        if r["Hr_Totale"] > 0 else 0,
        axis=1
    )

    return df_day.reset_index(drop=True)
