import streamlit as st
import pandas as pd
from datetime import datetime

from preprocessing.llti_preprocess import preprocess_llti


@st.cache_data(show_spinner="Chargement des données LLTI...")
def load_llti(file):
    return preprocess_llti(file)


def _llti_color(score: float):
    """Retourne (label, hex) selon le score en jours."""
    if pd.isna(score):
        return "—", "#808080"
    if score <= 7:
        return "Vert (≤7j)", "#2ca02c"
    if score <= 12:
        return "Orange (≤12j)", "#ff7f0e"
    if score <= 17:
        return "Jaune (≤17j)", "#d0a000"
    return "Rouge (>17j)", "#d62728"


def page_llti():
    st.header("📉 LLTI – Lagging Invoicing (Quartile)")

    uploaded = st.file_uploader(
        "Charger le fichier Business Object (BO) (Excel)",
        type=["xlsx"],
        key="llti_bo"
    )

    if not uploaded:
        st.info("Veuillez charger le fichier BO pour calculer le KPI LLTI.")
        return

    try:
        df = load_llti(uploaded)
    except ValueError as e:
        st.error(str(e))
        return

    if df.empty:
        st.warning("Aucune ligne Caterpillar trouvée pour le trimestre courant.")
        return

    # Calcul jours d'écart
    df["Days_diff"] = (df["Date Facture (Lignes)"] - df["Pointage dernière date (Segment)"]).dt.days

    # Score global (moyenne en jours calendaires)
    global_score = df["Days_diff"].mean()

    # Affichage score avec code couleur
    label, color = _llti_color(global_score)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("LLTI (moyenne en jours)", f"{global_score:.1f} jours")
    with col2:
        st.markdown(
            f"<div style='padding:10px;border-radius:6px;background:{color};color:#ffffff;display:inline-block'>{label}</div>",
            unsafe_allow_html=True
        )

    st.divider()

    # Tableau des facturations à la traîne
    st.subheader("Facturations à la traîne")

    or_summary = (
        df
        .groupby(["N° OR (Segment)", "Nom Client OR (or)"], as_index=False)
        .agg(
            avg_days=("Days_diff", "mean"),
            max_days=("Days_diff", "max"),
            n_invoices=("N° Facture (Lignes)", "nunique"),
            last_facture=("Date Facture (Lignes)", "max"),
            last_pointage=("Pointage dernière date (Segment)", "max"),
        )
        .sort_values("avg_days", ascending=False)
    )

    st.dataframe(
        or_summary.head(20).assign(
            avg_days=lambda d: d["avg_days"].round(1),
            max_days=lambda d: d["max_days"].astype(int)
        ),
        use_container_width=True
    )

    st.info(
        "Les OR listés ci-dessus sont triés par moyenne d'écart (Date Facture - Pointage). "
        "Utilisez cette liste pour prioriser les relances auprès des clients."
    )

    # Option export CSV
    csv = or_summary.to_csv(index=False)
    st.download_button("Télécharger le tableau (CSV)", csv, file_name="llti_facturations_a_la_traine.csv")