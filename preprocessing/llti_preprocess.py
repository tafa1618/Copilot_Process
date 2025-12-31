import pandas as pd

def preprocess_llti(df_bo: pd.DataFrame) -> pd.DataFrame:
    df = df_bo.copy()

    # ===============================
    # TYPAGE DES DATES
    # ===============================
    df["Date Facture (Lignes)"] = pd.to_datetime(
        df["Date Facture (Lignes)"], errors="coerce"
    )
    df["Pointage dernière date (Segment)"] = pd.to_datetime(
        df["Pointage dernière date (Segment)"], errors="coerce"
    )

    # ===============================
    # FILTRAGE MINIMUM VIABLE
    # ===============================
    df = df[
        df["N° Facture (Lignes)"].notna()
        & df["Date Facture (Lignes)"].notna()
        & df["Pointage dernière date (Segment)"].notna()
    ]

    # ===============================
    # AGRÉGATION PAR FACTURE (CLÉ)
    # ===============================
    df_facture = (
        df
        .groupby("N° Facture (Lignes)", as_index=False)
        .agg({
            "Date Facture (Lignes)": "max",
            "Pointage dernière date (Segment)": "max",
            "N° OR (Segment)": "first",
            "Nom Client OR (or)": "first",
            "Numéro série Equipement (Segment)": "first"
        })
    )

    # ===============================
    # CALCUL LLTI
    # ===============================
    df_facture["LLTI_jours"] = (
        df_facture["Date Facture (Lignes)"]
        - df_facture["Pointage dernière date (Segment)"]
    ).dt.days

    # ===============================
    # NETTOYAGE FINAL
    # ===============================
    df_facture = df_facture[df_facture["LLTI_jours"] >= 0]

    return df_facture
