# kpis/llti.py

import streamlit as st
import pandas as pd
from datetime import datetime

from preprocessing.llti_preprocess import preprocess_llti


def page_llti():
    st.header("💰 LLTI – Lead Time Facturation Service")
    st.caption(
        "⚠️ Indicateur **à titre indicatif** – basé sur les données BO et le dernier pointage connu."
    )

    st.divider()

    # ==================================================
    # UPLOAD
    # ==================================================
    uploaded_file = st.file_uploader(
        "Charger le fichier BO (facturation service)",
        type=["xlsx"],
        key="llti_bo_upload"
    )

    if not uploaded_file:
        st.info("Veuillez charger le fichier BO pour analyser le LLTI.")
        return

    # ==================================================
    # PREPROCESSING
    # ==================================================
    df = preprocess_llti(uploaded_file)

    if df.empty:
        st.warning("Aucune facture exploitable sur le trimestre en cours.")
        return

    # ==================================================
    # CALCUL LLTI (jours)
    # ==================================================
    df["Date Facture (Lignes)"] = pd.to_datetime(
        df["Date Facture (Lignes)"], errors="coerce"
    )
    df["Pointage dernière date (Segment)"] = pd.to_datetime(
        df["Pointage dernière date (Segment)"], errors="coerce"
    )

    df["LLTI_jours"] = (
        df["Date Facture (Lignes)"] -
        df["Pointage dernière date (Segment)"]
    ).dt.days

    # ==================================================
    # KPI GLOBAL
    # ==================================================
    llti_moyen = df["LLTI_jours"].mean()
    llti_mediane = df["LLTI_jours"].median()
    nb_factures = df["N° Facture (Lignes)"].nunique()

    col1, col2, col3 = st.columns(3)

    col1.metric("LLTI moyen (jours)", f"{llti_moyen:.1f}")
    col2.metric("LLTI médian (jours)", f"{llti_mediane:.0f}")
    col3.metric("Factures analysées", nb_factures)

    st.divider()

    # ==================================================
    # DISTRIBUTION LLTI
    # ==================================================
    st.subheader("Distribution du LLTI")

    st.bar_chart(
        df["LLTI_jours"].value_counts().sort_index()
    )

    st.divider()

    # ==================================================
    # TABLEAU DÉTAILLÉ (FACTURE PAR FACTURE)
    # ==================================================
    st.subheader("Détail LLTI – Facture par facture")

    df_display = df.sort_values(
        "LLTI_jours", ascending=False
    )

    st.dataframe(
        df_display,
        use_container_width=True
    )
