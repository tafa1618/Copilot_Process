import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def page_productivite():
    # ==================================================
    # STYLE
    # ==================================================
    sns.set_theme(style="whitegrid")

    # ==================================================
    # HEADER
    # ==================================================
    st.header("📊 Productivité & Exhaustivité – Pointages (Neemba Sénégal)")

    # ==================================================
    # UPLOAD
    # ==================================================
    uploaded_file = st.file_uploader(
        "Charger le fichier de pointages (Excel)",
        type=["xlsx"],
        key="productivite_pointages"
    )

    if not uploaded_file:
        st.info("Veuillez charger le fichier de pointages.")
        return

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
    COL_OR = "OR (Numéro)"

    # ==================================================
    # FILTRE GLOBAL PAR ÉQUIPE
    # ==================================================
    st.subheader("Filtrer par équipe")

    equipes_disponibles = sorted(df[COL_EQUIPE].dropna().unique())
    equipes_selectionnees = st.multiselect(
        "Choisir les équipes à analyser",
        options=equipes_disponibles,
        default=equipes_disponibles,
        key="productivite_equipes"
    )

    if equipes_selectionnees:
        df = df[df[COL_EQUIPE].isin(equipes_selectionnees)]

    st.divider()

    # ==================================================
    # PRÉPARATION DONNÉES
    # ==================================================
    df[COL_HEURES] = pd.to_numeric(df[COL_HEURES], errors="coerce").fillna(0)
    df[COL_FACTURABLE] = pd.to_numeric(df[COL_FACTURABLE], errors="coerce").fillna(0)
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")

    df["Heures_travaillées"] = df[COL_HEURES]
    df["Heures_facturables"] = df[COL_FACTURABLE]
    df["Mois"] = df[COL_DATE].dt.to_period("M").astype(str)
    df["Jour"] = df[COL_DATE].dt.day
    df["Jour_semaine"] = df[COL_DATE].dt.weekday  # 0=lundi

    # ==================================================
    # 1️⃣ EXHAUSTIVITÉ DES POINTAGES – CALENDRIER
    # ==================================================
    st.header("🗓️ Exhaustivité des pointages – Contrôle journalier")

    equipe_cal = st.selectbox(
        "Choisir une équipe à auditer",
        options=sorted(df[COL_EQUIPE].dropna().unique()),
        key="exhaustivite_equipe"
    )

    df_cal = df[df[COL_EQUIPE] == equipe_cal].copy()

    daily = (
        df_cal
        .groupby([COL_DATE, COL_TECHNICIEN])
        .agg(heures=("Heures_travaillées", "sum"))
        .reset_index()
    )

    daily["Jour"] = daily[COL_DATE].dt.day
    daily["Jour_semaine"] = daily[COL_DATE].dt.weekday

    def statut_pointage(row):
        h = row["heures"]
        wd = row["Jour_semaine"]

        if wd >= 5:  # Samedi / Dimanche
            return "Weekend OK" if h == 0 else "Travail weekend"
        else:
            if h == 0:
                return "Non conforme"
            elif h < 8:
                return "Incomplet"
            elif h == 8:
                return "Conforme"
            else:
                return "Surpointage"

    daily["Statut"] = daily.apply(statut_pointage, axis=1)

    pivot = daily.pivot(
        index="Jour",
        columns=COL_TECHNICIEN,
        values="Statut"
    )

    color_map = {
        "Non conforme": "#d73027",     # rouge
        "Incomplet": "#fee08b",        # jaune
        "Conforme": "#1a9850",         # vert
        "Surpointage": "#4575b4",      # bleu
        "Weekend OK": "#f0f0f0",       # gris
        "Travail weekend": "#984ea3"   # violet
    }

    color_matrix = pivot.applymap(lambda x: color_map.get(x, "#ffffff"))

    fig, ax = plt.subplots(
        figsize=(max(8, len(pivot.columns) * 0.6), 6)
    )

    ax.imshow(
        color_matrix.applymap(lambda c: list(mcolors.to_rgb(c))).values,
        aspect="auto"
    )
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")

    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    ax.set_xlabel("Techniciens")
    ax.set_ylabel("Jour du mois")
    ax.set_title(f"Exhaustivité des pointages – {equipe_cal}")

    st.pyplot(fig)
    st.divider()

   
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
    # PRODUCTIVITÉ PAR TECHNICIEN (BARPLOT)
    # ==================================================
    st.subheader("Productivité par technicien")

    prod_tech = (
        df.groupby(COL_TECHNICIEN)
        .agg(
            heures_trav=("Heures_travaillées", "sum"),
            heures_fact=("Heures_facturables", "sum")
        )
        .reset_index()
    )

    prod_tech["Productivité"] = (
        prod_tech["heures_fact"] / prod_tech["heures_trav"]
    )

    prod_tech = prod_tech.sort_values("Productivité", ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=prod_tech,
        x=COL_TECHNICIEN,
        y="Productivité",
        ax=ax
    )
    ax.set_title("Productivité par technicien")
    ax.set_ylabel("Productivité")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=45)

    st.pyplot(fig)

    st.dataframe(
        prod_tech.style.format({"Productivité": "{:.1%}"})
    )

    st.divider()

    # ==================================================
    # TIMELINE GLOBALE (LINEPLOT)
    # ==================================================
    st.subheader("Évolution mensuelle – Global")

    prod_mois_global = (
        df.groupby("Mois")
        .agg(
            heures_trav=("Heures_travaillées", "sum"),
            heures_fact=("Heures_facturables", "sum")
        )
        .reset_index()
        .sort_values("Mois")
    )

    prod_mois_global["Productivité globale"] = (
        prod_mois_global["heures_fact"] / prod_mois_global["heures_trav"]
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(
        data=prod_mois_global,
        x="Mois",
        y="Productivité globale",
        marker="o",
        ax=ax
    )

    ax.set_title("Évolution mensuelle de la productivité globale")
    ax.set_ylabel("Productivité")
    ax.set_xlabel("Mois")
    ax.tick_params(axis="x", rotation=45)

    st.pyplot(fig)

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
        options=sorted(df[COL_EQUIPE].dropna().unique()),
        key="productivite_focus_equipe"
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

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(
        data=comparaison,
        x="Mois",
        y="Productivité globale",
        label="Global",
        ax=ax
    )
    sns.lineplot(
        data=comparaison,
        x="Mois",
        y="Productivité équipe",
        label=equipe_choisie,
        ax=ax
    )

    ax.set_title(
        f"Comparaison de tendance – {equipe_choisie} vs Global"
    )
    ax.set_ylabel("Productivité")
    ax.set_xlabel("Mois")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()

    st.pyplot(fig)

    st.dataframe(
        comparaison.style.format({
            "Productivité globale": "{:.1%}",
            "Productivité équipe": "{:.1%}"
        })
    )
