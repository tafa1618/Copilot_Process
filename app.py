import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sandbox Process KPI", layout="wide")
st.title("Sandbox – Productivité & Efficience (Pointages)")

uploaded_file = st.file_uploader(
    "Charger le fichier de pointages (Excel)",
    type=["xlsx"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Aperçu des données")
    st.dataframe(df.head())

    st.divider()

    # 🔧 Mapping colonnes (à adapter si besoin)
    COL_TEMPS_POINTE = "Temps pointé"
    COL_TEMPS_VENDU = "Temps vendu"
    COL_TEMPS_PREVU = "Temps prévu devis"
    COL_TECHNICIEN = "Technicien"

    for col in [COL_TEMPS_POINTE, COL_TEMPS_VENDU, COL_TEMPS_PREVU]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Temps_utilisé"] = np.where(
        df[COL_TEMPS_VENDU].notna(),
        df[COL_TEMPS_VENDU],
        df[COL_TEMPS_PREVU]
    )

    df["Efficience"] = df["Temps_utilisé"] / df[COL_TEMPS_POINTE]

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["Efficience"])

    st.subheader("KPIs globaux")
    st.metric("Efficience moyenne", round(df["Efficience"].mean(), 2))
    st.metric("Nombre d’OR analysés", df.shape[0])

    st.subheader("Efficience par technicien")
    eff_tech = (
        df.groupby(COL_TECHNICIEN)["Efficience"]
        .mean()
        .sort_values(ascending=False)
    )

    st.bar_chart(eff_tech)

    st.subheader("Détail OR")
    st.dataframe(
        df[[COL_TECHNICIEN, COL_TEMPS_POINTE, "Temps_utilisé", "Efficience"]]
        .sort_values("Efficience")
    )
