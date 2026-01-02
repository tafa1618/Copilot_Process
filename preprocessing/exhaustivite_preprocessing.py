# preprocessing/exhaustivite_preprocessing.py

def compute_exhaustivite(df: pd.DataFrame) -> dict:
    """
    Exhaustivité basée sur Hr_Théorique (BI-approved)
    """

    def statut_pointage(hr_totale, hr_theorique, weekday):
        # Weekend
        if weekday >= 5:
            return "Weekend OK" if hr_totale == 0 else "Travail weekend"

        # Jour ouvré
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

    result = {}

    for mois, df_m in df.groupby("Mois"):
        result[mois] = {
            "statuts": df_m.pivot(
                index="Salarié - Nom",
                columns="Jour",
                values="Statut"
            ).fillna("").to_dict(orient="index"),

            "heures": df_m.pivot(
                index="Salarié - Nom",
                columns="Jour",
                values="Hr_Totale"
            ).fillna(0).to_dict(orient="index"),

            "teams": (
                df_m.groupby("Salarié - Nom")["Equipe3"]
                .first()
                .to_dict()
            )
        }

    return result
