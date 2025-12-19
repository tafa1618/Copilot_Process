import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


def page_productivite():
    # ==================================================
    # STYLE GRAPHIQUE
    # ==================================================
    sns.set_theme(style="whitegrid")

    # ==================================================
    # HEADER
    # ==================================================
    st.header("📊 Productivité – Pointages (Neemba Sénégal)")

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
    # 1️⃣ EXHAUSTIVITÉ DES POINTAGES – CALENDRIER
    # ==================================================
    st.header("🗓️ Exhaustivité des pointages")

    equipe_audit = st.selectbox(
        "Choisir une équipe à auditer",
        options=sorted(df[COL_EQUIPE].dropna().unique()),
        key="exhaustivite_equipe"
    )

    df_cal = df[df[COL_EQUIPE] == equipe_audit].copy()

    # --------------------------------------------------
    # AGRÉGATION : 1 ligne / jour / technicien
    # --------------------------------------------------
    daily = (
        df_cal
        .groupby([COL_DATE, COL_TECHNICIEN], as_index=False)
        .agg(
            heures=("Heures_travaillées", "sum"),
            jour_semaine=(COL_DATE, lambda x: x.iloc[0].weekday()),
            jour=(COL_DATE, lambda x: x.iloc[0].day)
        )
    )

    # --------------------------------------------------
    # RÈGLES MÉTIER – STATUT DU POINTAGE
    # --------------------------------------------------
    def statut_pointage(h, wd):
        if wd >= 5:  # samedi / dimanche
            return "Weekend OK" if h == 0 else "Travail weekend"
        if h == 0:
            return "Non conforme"
        if h < 8:
            return "Incomplet"
        if h == 8:
            return "Conforme"
        return "Surpointage"

    daily["Statut"] = daily.apply(
        lambda r: statut_pointage(r["heures"], r["jour_semaine"]),
        axis=1
    )

    # --------------------------------------------------
    # PIVOT (SÉCURISÉ)
    # --------------------------------------------------
    pivot = daily.pivot_table(
        index="jour",
        columns=COL_TECHNICIEN,
        values="Statut",
        aggfunc="first"
    )

    # --------------------------------------------------
    # MAPPING COULEURS
    # --------------------------------------------------
    colors = {
        "Non conforme": "#d73027",     # rouge
        "Incomplet": "#fee08b",        # jaune
        "Conforme": "#1a9850",         # vert
        "Surpointage": "#4575b4",      # bleu
        "Weekend OK": "#f0f0f0",       # gris
        "Travail weekend": "#984ea3"   # violet
    }

    # --------------------------------------------------
    # MATRICE RGB POUR IMAGESHOW
    # --------------------------------------------------
    rgb = np.zeros((pivot.shape[0], pivot.shape[1], 3), dtype=float)

    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            statut = pivot.iloc[i, j]
            couleur = colors.get(statut, "#ffffff")
            rgb[i, j, :] = mcolors.to_rgb(couleur)

    # --------------------------------------------------
    # VISUALISATION
    # --------------------------------------------------
    fig, ax = plt.subplots(
        figsize=(max(8, pivot.shape[1] * 0.6), 6)
    )

    ax.imshow(rgb, aspect="auto")

    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")

    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels(pivot.index)

    ax.set_xlabel("Techniciens")
    ax.set_ylabel("Jour du mois")
    ax.set_title(f"Exhaustivité des pointages – {equipe_audit}")

    st.pyplot(fig)
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
        # ==================================================
    # CORRÉLATION DES ÉQUIPES AVEC LA PRODUCTIVITÉ GLOBALE
    # ==================================================
    st.header("📈 Tendances & corrélation des équipes avec la moyenne")

    # --- Série globale mensuelle (référence) ---
    global_ts = (
        df.groupby("Mois")
        .agg(
            heures_trav=("Heures_travaillées", "sum"),
            heures_fact=("Heures_facturables", "sum")
        )
        .reset_index()
        .sort_values("Mois")
    )

    global_ts["Productivité globale"] = (
        global_ts["heures_fact"] / global_ts["heures_trav"]
    )

    # --- Équipes analysées ---
    equipes_corr = sorted(df[COL_EQUIPE].dropna().unique())

    correlations = []

    # Grille compacte (2 graphiques par ligne)
    NB_COLS = 2
    cols = st.columns(NB_COLS)

    for i, equipe in enumerate(equipes_corr):
        with cols[i % NB_COLS]:

            df_eq = df[df[COL_EQUIPE] == equipe]

            eq_ts = (
                df_eq.groupby("Mois")
                .agg(
                    heures_trav=("Heures_travaillées", "sum"),
                    heures_fact=("Heures_facturables", "sum")
                )
                .reset_index()
                .sort_values("Mois")
            )

            eq_ts["Productivité équipe"] = (
                eq_ts["heures_fact"] / eq_ts["heures_trav"]
            )

            # --- Fusion équipe vs global ---
            merged = pd.merge(
                global_ts[["Mois", "Productivité globale"]],
                eq_ts[["Mois", "Productivité équipe"]],
                on="Mois",
                how="inner"
            )

            # --- Corrélation ---
            corr = merged["Productivité globale"].corr(
                merged["Productivité équipe"]
            )

            correlations.append({
                "Équipe": equipe,
                "Corrélation": corr
            })

            # --- Plot ---
            fig, ax = plt.subplots(figsize=(4.5, 3))

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
                f"{equipe}\nCorrélation = {corr:.2f}",
                fontsize=10
            )
            ax.set_xlabel("")
            ax.set_ylabel("Productivité")
            ax.tick_params(axis="x", rotation=45)
            ax.legend(fontsize=8)

            st.pyplot(fig)

    # ==================================================
    # COMMENTAIRE AUTOMATIQUE – ÉQUIPE DRIVER
    # ==================================================
    if correlations:
        corr_df = pd.DataFrame(correlations).dropna()
        equipe_driver = corr_df.sort_values(
            "Corrélation", ascending=False
        ).iloc[0]

        st.info(
            f"📌 **Analyse d’influence**\n\n"
            f"L’équipe **{equipe_driver['Équipe']}** présente la plus forte "
            f"corrélation avec la productivité globale "
            f"(corrélation = {equipe_driver['Corrélation']:.2f}).\n\n"
            f"👉 Son évolution constitue un **bon proxy** de la tendance globale."
        )

