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
