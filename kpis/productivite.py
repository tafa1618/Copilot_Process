import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def page_productivite():
    sns.set_theme(style="whitegrid")

    st.header("📊 Productivité & Exhaustivité – Pointages")

    # ===============================
    # UPLOAD
    # ===============================
    uploaded_file = st.file_uploader(
        "Charger le fichier de pointages (Excel)",
        type=["xlsx"],
        key="pointages_upload"
    )

    if not uploaded_file:
        st.info("Veuillez charger le fichier de pointages.")
        return

    df = pd.read_excel(uploaded_file)

    st.subheader("Aperçu des données")
    st.dataframe(df.head())
    st.divider()

    # ===============================
    # COLONNES
    # ===============================
    COL_TECH = "Salarié - Nom"
    COL_EQUIPE = "Salarié - Equipe(Nom)"
    COL_HEURES = "Hr_travaillée"
    COL_FACT = "Facturable"
    COL_DATE = "Saisie heures - Date"

    # ===============================
    # FILTRE ÉQUIPE
    # ===============================
    equipes = sorted(df[COL_EQUIPE].dropna().unique())
    equipes_sel = st.multiselect(
        "Filtrer par équipe",
        options=equipes,
        default=equipes
    )

    if equipes_sel:
        df = df[df[COL_EQUIPE].isin(equipes_sel)]

    st.divider()

    # ===============================
    # PRÉPARATION
    # ===============================
    df[COL_HEURES] = pd.to_numeric(df[COL_HEURES], errors="coerce").fillna(0)
    df[COL_FACT] = pd.to_numeric(df[COL_FACT], errors="coerce").fillna(0)
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")

    df["Heures_trav"] = df[COL_HEURES]
    df["Heures_fact"] = df[COL_FACT]
    df["Jour"] = df[COL_DATE].dt.day
    df["Jour_semaine"] = df[COL_DATE].dt.weekday
    df["Mois"] = df[COL_DATE].dt.to_period("M").astype(str)

    # ===============================
  # ==================================================
        # ==================================================
    # 1️⃣ EXHAUSTIVITÉ DES POINTAGES – CALENDRIER
    # ==================================================
    st.header("🗓️ Exhaustivité des pointages")

    equipe_audit = st.selectbox(
        "Choisir une équipe à auditer",
        options=sorted(df[COL_EQUIPE].dropna().unique())
    )

    df_cal = df[df[COL_EQUIPE] == equipe_audit].copy()

    # --------------------------------------------------
    # AGRÉGATION : 1 ligne / jour / technicien
    # --------------------------------------------------
    daily = (
        df_cal
        .groupby([COL_DATE, COL_TECH], as_index=False)
        .agg(
            heures=("Heures_trav", "sum"),
            jour_semaine=(COL_DATE, lambda x: x.iloc[0].weekday()),
            jour=(COL_DATE, lambda x: x.iloc[0].day)
        )
    )

    # --------------------------------------------------
    # STATUT MÉTIER
    # --------------------------------------------------
    def statut_pointage(h, wd):
        if wd >= 5:  # Samedi / Dimanche
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
    # PIVOT SÉCURISÉ
    # --------------------------------------------------
    pivot = daily.pivot_table(
        index="jour",
        columns=COL_TECH,
        values="Statut",
        aggfunc="first"
    )

    # --------------------------------------------------
    # COULEURS
    # --------------------------------------------------
    colors = {
        "Non conforme": "#d73027",
        "Incomplet": "#fee08b",
        "Conforme": "#1a9850",
        "Surpointage": "#4575b4",
        "Weekend OK": "#f0f0f0",
        "Travail weekend": "#984ea3"
    }

    color_matrix = pivot.applymap(lambda x: colors.get(x, "#ffffff"))

    # --------------------------------------------------
    # VISUALISATION
    # --------------------------------------------------
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
    ax.set_title(f"Exhaustivité des pointages – {equipe_audit}")

    st.pyplot(fig)
    st.divider()

    # ===============================
    # 2️⃣ PRODUCTIVITÉ GLOBALE
    # ===============================
    total_trav = df["Heures_trav"].sum()
    total_fact = df["Heures_fact"].sum()
    prod_globale = total_fact / total_trav if total_trav > 0 else 0

    # 🔗 Stockage pour l’accueil
    st.session_state.productivite_globale = prod_globale
    st.session_state.productivite_calculee = True

    st.subheader("Productivité globale")
    st.metric("Productivité", f"{prod_globale:.1%}")
    st.divider()

    # ===============================
    # PRODUCTIVITÉ PAR TECHNICIEN
    # ===============================
    prod_tech = (
        df.groupby(COL_TECH)
        .agg(
            heures_trav=("Heures_trav", "sum"),
            heures_fact=("Heures_fact", "sum")
        )
        .reset_index()
    )

    prod_tech["Productivité"] = (
        prod_tech["heures_fact"] / prod_tech["heures_trav"]
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=prod_tech.sort_values("Productivité", ascending=False),
        x=COL_TECH,
        y="Productivité",
        ax=ax
    )
    ax.set_title("Productivité par technicien")
    ax.tick_params(axis="x", rotation=45)

    st.pyplot(fig)
    st.dataframe(prod_tech.style.format({"Productivité": "{:.1%}"}))
