# kpis/llti.py

import streamlit as st
import pandas as pd

from preprocessing.llti_preprocess import preprocess_llti


def page_llti():
    st.header("💰 LLTI – Lead Time Facturation Service")
    st.caption(
        "⚠️ Indicateur à titre **indicatif** – basé sur la facturation BO "
        "et le dernier pointage connu. Certaines données peuvent être perdues "
        "lors des consolidations."
    )

    st.divider()

    # ==================================================
    # UPLOAD BO
    # ==================================================
    uploaded_file = st.file_uploader(
        "Charger le fichier BO – Facturation Service",
        type=["xlsx"],
        key="llti_bo_upload"
    )

    if not uploaded_file:
        st.info("Veuillez charger le fichier BO pour analyser le LLTI.")
        return

    # ==================================================
    # LECTURE + PREPROCESSING
    # ==================================================
    try:
        df_bo = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Erreur de lecture du fichier : {e}")
        return

    df_llti = preprocess_llti(df_bo)

    if df_llti.empty:
        st.warning("Aucune facture exploitable sur le trimestre en cours.")
        return

    # ==================================================
    # KPI GLOBAL
    # ==================================================
    llti_moyen = df_llti["LLTI_jours"].mean()
    llti_mediane = df_llti["LLTI_jours"].median()
    nb_factures = df_llti["N° Facture (Lignes)"].nunique()

    col1, col2, col3 = st.columns(3)

    col1.metric("LLTI moyen (jours)", f"{llti_moyen:.1f}")
    col2.metric("LLTI médian (jours)", f"{llti_mediane:.0f}")
    col3.metric("Factures analysées", f"{nb_factures}")

    st.divider()

    # ==================================================
    # DISTRIBUTION
    # ==================================================
    st.subheader("Distribution du LLTI (jours)")

    st.bar_chart(
        df_llti["LLTI_jours"]
        .value_counts()
        .sort_index()
    )

    st.divider()

    # ==================================================
    # TABLEAU DÉTAILLÉ
    # ==================================================
    st.subheader("Détail LLTI – Facture par facture")

    df_display = df_llti.sort_values(
        "LLTI_jours", ascending=False
    )

    st.dataframe(
        df_display,
        use_container_width=True
    )
