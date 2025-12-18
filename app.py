import streamlit as st
import pandas as pd
import numpy as np

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Sandbox Productivité", layout="wide")
st.title("Sandbox – Productivité (Pointages Neemba Sénégal)")

# ==================================================
# UPLOAD
# ==================================================
uploaded_file = st.file_uploader(
    "Charger le fichier de pointages (Excel)",
    type=["xlsx"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Aperçu des données")
    st.dataframe(df.head())
    st.divider()

    # ==================================================
    # CONSTANTES COLONNES
    # ==================================================
    COL_TECHNICIEN = "Salarié - Nom"
    COL_EQUIPE = "Salarié - Equipe(Nom)"
    COL_FACTURABLE = "Facturable"
    COL_HEURES = "Hr_travaillée"
    COL_DATE = "Saisie heures - Date"

    # ==================================================
    # FILTRE GLOBAL PAR ÉQUIPE
    # ==================================================
    st.subheader("Filtrer par équipe")

    equipes_disponibles = sorted(df[COL_EQUIPE].dropna().unique())
    equipes_selectionnees = st.multiselect(
        "Choisir les équipes à analyser",
        options=equipes_disponibles,
        default=equipes_disponibles
    )

    if equipes_selectionnees:
        df = df[df[COL_EQUIPE].isin(equipes_selectionnees)]

    st.divider()

    # ==================================================
    # PRÉPARATION DONNÉES
    # ==================================================
    df[COL_HEURES] = pd.to_numeric(df[COL_HEURES], errors="coerce")
    df[COL_FACTURABLE] = pd.to_numeric(df[COL_FACTURABLE], errors="coerce").fillna(0)
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")

    df["Heures_travaillées"] = df[COL_HEURES]
    df["Heures_facturables"] = df[COL_FACTURABLE]
    df["Mois"] = df[COL_DATE].dt.to_period("M").astype(str)

    # ==================================================
    # KPI GLOBAL
    # ==================================================
    total_trav = df["Heures_travaillées"].sum()
    total_fact = df["Heures_facturables"].sum()
    prod_global = total_fact / total_trav if total_trav > 0 else 0

    st.subheader("Productivité globale")
    st.metric("Productivité", f"{prod_global:.1%}")
    st.divider()

    # ==================================================
    # PRODUCTIVITÉ PAR TECHNICIEN
    # ==================================================
    st.subheader("Productivité par technicien")

    prod_tech = (
        df.groupby(COL_TECHNICIEN)
        .agg(
            heures_trav=("Heures_travaillées", "sum"),
            heures_fact=("Heures_facturables", "sum")
        )
    )

    prod_tech["Productivité"] = prod_tech["heures_fact"] / prod_tech["heures_trav"]
    prod_tech = prod_tech.sort_values("Productivité", ascending=False)

    st.bar_chart(prod_tech["Productivité"])
    st.dataframe(prod_tech.style.format({"Productivité": "{:.1%}"}))
    st.divider()

    # ==================================================
    # TIMELINE GLOBALE
    # ==================================================
    st.subheader("Évolution mensuelle – Global")

    prod_mois = (
        df.groupby("Mois")
        .agg(
            heures_trav=("Heures_travaillées", "sum"),
            heures_fact=("Heures_facturables", "sum")
        )
        .reset_index()
    )

    prod_mois["Productivité"] = prod_mois["heures_fact"] / prod_mois["heures_trav"]
    prod_mois = prod_mois.sort_values("Mois")

    st.line_chart(prod_mois.set_index("Mois")["Productivité"])
    st.dataframe(prod_mois.style.format({"Productivité": "{:.1%}"}))
    st.divider()

    # ==================================================
    # ANALYSE FOCALISÉE – UNE ÉQUIPE
    # ==================================================
    st.header("Analyse détaillée d’une équipe")

    equipe_choisie = st.selectbox(
        "Choisir une équipe",
        options=sorted(df[COL_EQUIPE].dropna().unique())
    )

    df_eq = df[df[COL_EQUIPE] == equipe_choisie]

    heures_trav_eq = df_eq["Heures_travaillées"].sum()
    heures_fact_eq = df_eq["Heures_facturables"].sum()
    prod_eq = heures_fact_eq / heures_trav_eq if heures_trav_eq > 0 else 0

    st.metric(f"Productivité – {equipe_choisie}", f"{prod_eq:.1%}")

    prod_mois_eq = (
        df_eq.groupby("Mois")
        .agg(
            heures_trav=("Heures_travaillées", "sum"),
            heures_fact=("Heures_facturables", "sum")
        )
        .reset_index()
    )

    prod_mois_eq["Productivité"] = prod_mois_eq["heures_fact"] / prod_mois_eq["heures_trav"]
    prod_mois_eq = prod_mois_eq.sort_values("Mois")

    st.subheader("Évolution mensuelle – équipe sélectionnée")
    st.line_chart(prod_mois_eq.set_index("Mois")["Productivité"])
    st.dataframe(prod_mois_eq.style.format({"Productivité": "{:.1%}"}))
