import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


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

    prod_mois_global = (
        df.groupby("Mois")
        .agg(
            heures_trav=("Heures_travaillées", "sum"),
            heures_fact=("Heures_facturables", "sum")
        )
        .reset_index()
    )

    prod_mois_global["Productivité globale"] = (
        prod_mois_global["heures_fact"] / prod_mois_global["heures_trav"]
    )

    prod_mois_global = prod_mois_global.sort_values("Mois")

    st.line_chart(
        prod_mois_global.set_index("Mois")["Productivité globale"]
    )

    st.dataframe(
        prod_mois_global.style.format({"Productivité globale": "{:.1%}"})
    )
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

    st.metric(
        f"Productivité – {equipe_choisie}",
        f"{prod_eq:.1%}"
    )

    # ==================================================
    # COMPARAISON TIMELINE – ÉQUIPE vs GLOBAL
    # ==================================================
    prod_mois_eq = (
        df_eq.groupby("Mois")
        .agg(
            heures_trav=("Heures_travaillées", "sum"),
            heures_fact=("Heures_facturables", "sum")
        )
        .reset_index()
    )

    prod_mois_eq["Productivité équipe"] = (
        prod_mois_eq["heures_fact"] / prod_mois_eq["heures_trav"]
    )

    comparaison = pd.merge(
        prod_mois_global[["Mois", "Productivité globale"]],
        prod_mois_eq[["Mois", "Productivité équipe"]],
        on="Mois",
        how="inner"
    ).sort_values("Mois")

    st.subheader(f"Évolution mensuelle – {equipe_choisie} vs Global")

    st.line_chart(
        comparaison.set_index("Mois")
    )

    st.dataframe(
        comparaison.style.format({
            "Productivité globale": "{:.1%}",
            "Productivité équipe": "{:.1%}"
        })
    )
    
    # ==================================================
    # TENDANCES & INFLUENCE DES ÉQUIPES
    # ==================================================
    st.header("Tendances et influence des équipes")
    
    # Calcul productivité globale mensuelle (déjà existante logiquement)
    global_ts = (
        df.groupby("Mois")
        .agg(
            heures_trav=("Heures_travaillées", "sum"),
            heures_fact=("Heures_facturables", "sum")
        )
        .reset_index()
    )
    
    global_ts["Productivité globale"] = (
        global_ts["heures_fact"] / global_ts["heures_trav"]
    )
    
    resultats_corr = []
    
    # Une figure par équipe
    for equipe in sorted(df[COL_EQUIPE].unique()):
    
        df_eq = df[df[COL_EQUIPE] == equipe]
    
        eq_ts = (
            df_eq.groupby("Mois")
            .agg(
                heures_trav=("Heures_travaillées", "sum"),
                heures_fact=("Heures_facturables", "sum")
            )
            .reset_index()
        )
    
        eq_ts["Productivité équipe"] = (
            eq_ts["heures_fact"] / eq_ts["heures_trav"]
        )
    
        # Fusion pour corrélation
        merged = pd.merge(
            global_ts[["Mois", "Productivité globale"]],
            eq_ts[["Mois", "Productivité équipe"]],
            on="Mois",
            how="inner"
        )
    
        # Corrélation
        corr = merged["Productivité globale"].corr(
            merged["Productivité équipe"]
        )
    
        resultats_corr.append({
            "Équipe": equipe,
            "Corrélation avec le global": corr
        })
    
        # ====== PLOT ======
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.lineplot(
            data=merged,
            x="Mois",
            y="Productivité globale",
            label="Global",
            ax=ax
        )
        sns.lineplot(
            data=merged,
            x="Mois",
            y="Productivité équipe",
            label=equipe,
            ax=ax
        )
    
        ax.set_title(
            f"Tendance – {equipe} (corrélation = {corr:.2f})"
        )
        ax.set_ylabel("Productivité")
        ax.set_xlabel("Mois")
        ax.legend()
    
        st.pyplot(fig)
    
