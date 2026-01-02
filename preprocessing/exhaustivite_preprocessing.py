# preprocessing/exhaustivite_preprocessing.py

import pandas as pd


def compute_exhaustivite(df: pd.DataFrame) -> dict:
    """
    Calcule l'exhaustivité journalière
    Retourne une structure prête pour heatmap / table
    """

    def statut_pointage(hr_totale, hr_theorique, weekday):
        # Weekend
        if weekday >= 5:
            return "Weekend OK" if hr_totale == 0 else "Travail weekend"

        # Jours ouvrés
        if hr_theorique > 0 and hr_totale == 0:
            return "Non conforme"
        if hr_totale < hr_theorique:
            return "Incomplet"
        if hr_totale == hr_theorique:
            return "Conforme"
        return "Surpointage"

    df = df.copy()

    df["Statut"] = df.apply(
        lambda r: statut_pointage(
            r["Hr_Totale"],
            r["Hr_Théorique"],
            r["Jour_semaine"]
        ),
        axis=1
    )

    # ===============================
    # STRUCTURE PAR MOIS
    # ===============================
    result = {}

    for mois, df_m in df.groupby("Mois"):
        pivot_statut = df_m.pivot_table(
            index="Salarié - Nom",
            columns="Jour",
            values="Statut",
            aggfunc="first"
        )

        pivot_heures = df_m.pivot_table(
            index="Salarié - Nom",
            columns="Jour",
            values="Hr_Totale",
            aggfunc="sum"
        )

        teams = (
            df_m.groupby("Salarié - Nom")["Salarié - Equipe(Nom)"]
            .first()
            .to_dict()
        )

        result[mois] = {
            "statuts": pivot_statut.fillna("").to_dict(orient="index"),
            "heures": pivot_heures.fillna(0).to_dict(orient="index"),
            "teams": teams
        }

    return result
