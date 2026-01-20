import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from preprocessing.inspection_preprocess import compute_inspection_rate


@st.cache_data(show_spinner="Chargement des fichiers d'inspection...")
def load_any(file):
    return file


def page_inspection():
    sns.set_theme(style="whitegrid")

    st.header("🔍 Inspection Rate")

    st.info(
        "Chargez le fichier BO (factures), le fichier Cat Inspect (inspections réalisées) et éventuellement le fichier de pointages pour rapprocher les techniciens."
    )

    bo_file = st.file_uploader("Charger le fichier BO (Excel)", type=["xlsx", "xls"], key="inspection_bo")
    inspect_file = st.file_uploader("Charger le fichier Cat Inspect (Excel ou CSV)", type=["xlsx", "xls", "csv"], key="inspection_cat")
    pointage_file = st.file_uploader("(Optionnel) Charger le fichier de pointages (Excel)", type=["xlsx", "xls"], key="inspection_pointages")

    if not bo_file or not inspect_file:
        st.warning("Les fichiers BO et Cat Inspect sont requis pour calculer l'Inspection Rate.")
        return

    try:
        rate, df_res = compute_inspection_rate(bo_file, inspect_file, pointage_file)
    except Exception as exc:
        st.error(f"Erreur lors du calcul: {exc}")
        return

    st.subheader("KPI global")
    st.metric("Inspection Rate (factures inspectées)", f"{rate:.1%}")

    st.divider()

    st.subheader("Détails par facture")
    st.write(
        "Tableau résumant pour chaque facture : ORs, Serials, si inspectée, méthode trouvée, date(s) d'inspection, inspecteurs, techniciens pointés (si fournis)."
    )

    st.dataframe(df_res)

    # Résumé par méthode
    st.divider()
    st.subheader("Répartition des factures par résultat")
    summary = (
        df_res.groupby("Method").agg(
            nb_factures=("N° Facture", "count"),
            inspectees=("Inspected", "sum")
        )
    ).reset_index()
    st.dataframe(summary)

    st.divider()
    st.subheader("Insights par Technicien et Équipe")
    if pointage_file is not None and not df_res["PointageRecords"].isna().all():
        # Analyser par technicien et équipe
        tech_team_insights = []
        for _, row in df_res.iterrows():
            if pd.notna(row["PointageRecords"]):
                records = [r.strip() for r in row["PointageRecords"].split(",")]
                for record in records:
                    parts = [p.strip() for p in record.split(";")]
                    tech = None
                    team = None
                    for part in parts:
                        if not part.startswith("OR:"):
                            if tech is None:
                                tech = part
                            else:
                                team = part
                    if tech:
                        tech_team_insights.append({
                            "Technicien": tech,
                            "Equipe": team if team else "Non spécifiée",
                            "Facture": row["N° Facture"],
                            "Inspected": row["Inspected"],
                            "Method": row["Method"]
                        })
        if tech_team_insights:
            df_tech_team = pd.DataFrame(tech_team_insights)
            # Par technicien
            tech_summary = df_tech_team.groupby("Technicien").agg(
                nb_factures=("Facture", "count"),
                inspectees=("Inspected", "sum"),
                taux_inspection=("Inspected", "mean")
            ).reset_index()
            tech_summary["Taux Inspection"] = (tech_summary["taux_inspection"] * 100).round(1).astype(str) + "%"
            tech_summary = tech_summary.sort_values("taux_inspection", ascending=False)
            st.write("**Performance par Technicien :**")
            st.dataframe(tech_summary[["Technicien", "nb_factures", "inspectees", "Taux Inspection"]])

            # Par équipe
            team_summary = df_tech_team.groupby("Equipe").agg(
                nb_factures=("Facture", "count"),
                inspectees=("Inspected", "sum"),
                taux_inspection=("Inspected", "mean")
            ).reset_index()
            team_summary["Taux Inspection"] = (team_summary["taux_inspection"] * 100).round(1).astype(str) + "%"
            team_summary = team_summary.sort_values("taux_inspection", ascending=False)
            st.write("**Performance par Équipe :**")
            st.dataframe(team_summary[["Equipe", "nb_factures", "inspectees", "Taux Inspection"]])

            # Visualisations
            col1, col2 = st.columns(2)
            with col1:
                fig, ax = plt.subplots(figsize=(6, 4))
                tech_summary.set_index("Technicien")["taux_inspection"].plot(kind="bar", ax=ax)
                ax.set_ylabel("Taux d'Inspection")
                ax.set_title("Taux d'Inspection par Technicien")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig)
            with col2:
                fig, ax = plt.subplots(figsize=(6, 4))
                team_summary.set_index("Equipe")["taux_inspection"].plot(kind="bar", ax=ax)
                ax.set_ylabel("Taux d'Inspection")
                ax.set_title("Taux d'Inspection par Équipe")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig)
        else:
            st.info("Aucune donnée de technicien ou équipe disponible dans les pointages.")
    else:
        st.info("Fichier de pointages non fourni ou aucune donnée trouvée.")

    st.divider()
    st.markdown("**Export** : télécharger le tableau détaillé au format CSV")
    csv = df_res.to_csv(index=False).encode("utf-8")
    st.download_button("Télécharger CSV", data=csv, file_name="inspection_rate_details.csv")

    # Petite visualisation
    if not df_res.empty:
        fig, ax = plt.subplots(figsize=(6, 3))
        df_plot = df_res.copy()
        df_plot["Method"] = df_plot["Method"].fillna("None")
        counts = df_plot.groupby("Method")["N° Facture"].count()
        if counts.empty:
            st.info("Aucune donnée disponible pour la visualisation (pas de méthode identifiée).")
        else:
            counts.plot(kind="bar", ax=ax)
            ax.set_ylabel("Nombre de factures")
            ax.set_title("Répartition par méthode d'identification")
            st.pyplot(fig)
