import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


# ==================================================
# UTILITAIRE : DÉTECTION COLONNE OR
# ==================================================
def detect_or_column(df):
    candidats = [
        "N° OR (Segment)",
        "N° OR",
        "OR (Numéro)",
        "OR",
        "Numéro OR"
    ]
    for col in candidats:
        if col in df.columns:
            return col
    return None


# ==================================================
# PAGE EFFICIENCE
# ==================================================
def page_efficience():

    sns.set_theme(style="whitegrid")

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------
    st.header("⚙️ Efficience des OR – Pilotage Méthode & Process")

    st.markdown(
        """
        **Définition**  
        L’efficience mesure l’écart entre le **temps consommé** et le
        **temps vendu ou prévu** sur un Ordre de Réparation (OR).

        👉 OR *en cours* = **actionnable**  
        👉 OR *clôturé* = **historique**
        """
    )

    st.divider()

    # --------------------------------------------------
    # UPLOAD FICHIERS
    # --------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        file_bo = st.file_uploader(
            "📄 Base BO (OR)",
            type=["xlsx"],
            key="eff_bo"
        )

    with col2:
        file_pt = st.file_uploader(
            "⏱️ Pointages",
            type=["xlsx"],
            key="eff_pt"
        )

    with col3:
        file_ie = st.file_uploader(
            "📌 Extraction IE (statut OR)",
            type=["xlsx"],
            key="eff_ie"
        )

    if not (file_bo and file_pt and file_ie):
        st.info("Veuillez charger les **3 fichiers** pour lancer l’analyse.")
        return

    # --------------------------------------------------
    # LECTURE DONNÉES
    # --------------------------------------------------
    df_bo = pd.read_excel(file_bo)
    df_pt = pd.read_excel(file_pt)
    df_ie = pd.read_excel(file_ie)

    # --------------------------------------------------
    # DÉTECTION & NORMALISATION OR
    # --------------------------------------------------
    col_or_bo = detect_or_column(df_bo)
    col_or_pt = detect_or_column(df_pt)
    col_or_ie = detect_or_column(df_ie)

    if not (col_or_bo and col_or_pt and col_or_ie):
        st.error("Impossible de détecter la colonne OR dans un des fichiers.")
        return

    df_bo = df_bo.rename(columns={col_or_bo: "OR_ID"})
    df_pt = df_pt.rename(columns={col_or_pt: "OR_ID"})
    df_ie = df_ie.rename(columns={col_or_ie: "OR_ID"})

    # --------------------------------------------------
    # COLONNES MÉTIER
    # --------------------------------------------------
    COL_EQUIPE = "Salarié - Equipe(Nom)"
    COL_TECH = "Salarié - Nom"

    COL_TEMPS_VENDU = "Temps vendu (OR)"
    COL_TEMPS_PREVU = "Temps prévu devis (OR)"
    COL_TEMPS_CONSO = "Durée pointage agents productifs (OR)"

    COL_STATUT = "Position"
    COL_TYPE_OR = "Type OR"

    # --------------------------------------------------
    # PRÉPARATION BO
    # --------------------------------------------------
    for col in [COL_TEMPS_VENDU, COL_TEMPS_PREVU, COL_TEMPS_CONSO]:
        df_bo[col] = pd.to_numeric(df_bo[col], errors="coerce")

    df_bo["Temps_reference"] = df_bo[COL_TEMPS_VENDU].fillna(
        df_bo[COL_TEMPS_PREVU]
    )

    df_bo = df_bo[df_bo["Temps_reference"] > 0]

    # --------------------------------------------------
    # MERGE BO + IE
    # --------------------------------------------------
    df = df_bo.merge(
        df_ie[["OR_ID", COL_STATUT]],
        on="OR_ID",
        how="left"
    )

    # --------------------------------------------------
    # CALCUL EFFICIENCE
    # --------------------------------------------------
    df["Efficience"] = df[COL_TEMPS_CONSO] / df["Temps_reference"]

    st.divider()

    # --------------------------------------------------
    # KPI GLOBAUX
    # --------------------------------------------------
    st.subheader("📊 Efficience globale")

    col1, col2, col3 = st.columns(3)

    col1.metric("Efficience moyenne", f"{df['Efficience'].mean():.1%}")
    col2.metric("OR ≤ 100%", f"{(df['Efficience'] <= 1).mean():.1%}")
    col3.metric("OR > 120%", f"{(df['Efficience'] > 1.2).mean():.1%}")

    st.divider()

    # --------------------------------------------------
    # EFFICIENCE PAR ÉQUIPE
    # --------------------------------------------------
    st.subheader("🏭 Efficience par équipe")

    eff_equipe = (
        df.groupby(COL_EQUIPE)
        .agg(
            efficience=("Efficience", "mean"),
            nb_or=("OR_ID", "count")
        )
        .reset_index()
        .sort_values("efficience", ascending=False)
    )

    st.dataframe(
        eff_equipe.style.format({"efficience": "{:.1%}"})
    )

    st.divider()

    # --------------------------------------------------
    # TOP / FLOP TECHNICIENS (COACHING)
    # --------------------------------------------------
    st.subheader("🧑‍🔧 Coaching techniciens")

    eff_tech = (
        df.groupby(COL_TECH)
        .agg(
            efficience=("Efficience", "mean"),
            nb_or=("OR_ID", "count")
        )
        .reset_index()
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔝 Top efficience")
        st.dataframe(
            eff_tech.sort_values("efficience").head(5)
            .style.format({"efficience": "{:.1%}"})
        )

    with col2:
        st.markdown("### ⚠️ À accompagner")
        st.dataframe(
            eff_tech.sort_values("efficience", ascending=False).head(5)
            .style.format({"efficience": "{:.1%}"})
        )

    st.divider()

    # --------------------------------------------------
    # ENCOURS ACTIONNABLES
    # --------------------------------------------------
    st.subheader("🚨 OR en cours – dérives actionnables")

    equipes = sorted(df[COL_EQUIPE].dropna().unique())
    equipe_sel = st.selectbox("Filtrer par équipe", options=equipes)

    encours = df[
        (df[COL_STATUT] != "Clôturé") &
        (df[COL_EQUIPE] == equipe_sel) &
        (df["Efficience"] > 1)
    ]

    st.dataframe(
        encours[
            [
                "OR_ID",
                COL_EQUIPE,
                COL_TYPE_OR,
                "Temps_reference",
                COL_TEMPS_CONSO,
                "Efficience",
                COL_STATUT
            ]
        ]
        .sort_values("Efficience", ascending=False)
        .style.format({"Efficience": "{:.1%}"})
    )


