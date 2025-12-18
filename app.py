import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sandbox Productivité", layout="wide")
st.title("Sandbox – Productivité (Pointages)")

uploaded_file = st.file_uploader(
    "Charger le fichier de pointages (Excel)",
    type=["xlsx"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Aperçu des données")
    st.dataframe(df.head())

    st.divider()

    # =====================
    # Mapping colonnes EXACT
    # =====================
    COL_TECHNICIEN = "Salarié - Nom"
    COL_EQUIPE = "Salarié - Equipe(Nom)"
    COL_OR = "OR (Numéro)"
    COL_FACTURABLE = "Facturable"       # NUMÉRIQUE (heures)
    COL_HEURES = "Hr_travaillée"

    # Sécurisation types
    df[COL_HEURES] = pd.to_numeric(df[COL_HEURES], errors="coerce")
    df[COL_FACTURABLE] = pd.to_numeric(df[COL_FACTURABLE], errors="coerce").fillna(0)

    # Calcul heures
    df["Heures_travaillées"] = df[COL_HEURES]
    df["Heures_facturables"] = df[COL_FACTURABLE]

    # =====================
    # KPI global
    # =====================
    total_travaille = df["Heures_travaillées"].sum()
    total_facturable = df["Heures_facturables"].sum()

    productivite_globale = (
        total_facturable / total_travaille
        if total_travaille > 0 else 0
    )

    st.subheader("Productivité globale")
    st.metric("Productivité", f"{productivite_globale:.1%}")

    st.divider()

    # =====================
    # Productivité par technicien
    # =====================
    st.subheader("Productivité par technicien")

    prod_tech = (
        df.groupby(COL_TECHNICIEN)
        .agg(
            heures_travaillees=("Heures_travaillées", "sum"),
            heures_facturables=("Heures_facturables", "sum")
        )
    )

    prod_tech["Productivité"] = (
        prod_tech["heures_facturables"] /
        prod_tech["heures_travaillees"]
    )

    prod_tech = prod_tech.sort_values("Productivité", ascending=False)

    st.bar_chart(prod_tech["Productivité"])

    st.divider()

    # =====================
    # Productivité par équipe
    # =====================
    st.subheader("Productivité par équipe")

    prod_equipe = (
        df.groupby(COL_EQUIPE)
        .agg(
            heures_travaillees=("Heures_travaillées", "sum"),
            heures_facturables=("Heures_facturables", "sum")
        )
    )

    prod_equipe["Productivité"] = (
        prod_equipe["heures_facturables"] /
        prod_equipe["heures_travaillees"]
    )

    prod_equipe = prod_equipe.sort_values("Productivité", ascending=False)

    st.bar_chart(prod_equipe["Productivité"])

    st.divider()

    # =====================
    # Tableau détail
    # =====================
    st.subheader("Détail productivité (Technicien)")

    st.dataframe(
        prod_tech
        .reset_index()
        .style.format({"Productivité": "{:.1%}"})
    )

