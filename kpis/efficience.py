import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def page_efficience():
    sns.set_theme(style="whitegrid")

    # ==================================================
    # HEADER
    # ==================================================
    st.header("⚙️ Efficience des OR – Pilotage Méthode & Process")

    st.markdown(
        """
        **Définition**  
        L’efficience mesure l’écart entre le **temps consommé** et le **temps vendu ou prévu**
        sur un Ordre de Réparation (OR).

        👉 Les OR *en cours* sont **actionnables**  
        👉 Les OR *clôturés* servent de **retour d’expérience**
        """
    )

    st.divider()

    # ==================================================
    # UPLOAD DES FICHIERS
    # ==================================================
    col1, col2, col3 = st.columns(3)

    with col1:
        file_bo = st.file_uploader(
            "📄 Base BO (OR)",
            type=["xlsx"],
            key="eff_bo"
        )

    with col2:
        file_pointage = st.file_uploader(
            "⏱️ Pointages",
            type=["xlsx"],
            key="eff_pointage"
        )

    with col3:
        file_ie = st.file_uploader(
            "📌 Extraction IE (statut OR)",
            type=["xlsx"],
            key="eff_ie"
        )

    if not (file_bo and file_pointage and file_ie):
        st.info("Veuillez charger les **3 fichiers** pour lancer l’analyse.")
        return

    # ==================================================
    # LECTURE DES DONNÉES
    # ==================================================
    df_bo = pd.read_excel(file_bo)
    df_pt = pd.read_excel(file_pointage)
    df_ie = pd.read_excel(file_ie)

    # ==================================================
    # NORMALISATION COLONNES
    # ==================================================
    COL_OR = "N° OR (Segment)"
    COL_EQUIPE = "Salarié - Equipe(Nom)"
    COL_TECH = "Salarié - Nom"

    COL_TEMPS_VENDU = "Temps vendu (OR)"
    COL_TEMPS_PREVU = "Temps prévu devis (OR)"
    COL_TEMPS_CONSO = "Durée pointage agents productifs (OR)"

    COL_STATUT = "Position"  # IE
    COL_TYPE_OR = "Type OR"

    # ==================================================
    # PRÉPARATION BO
    # ==================================================
    df_bo[COL_TEMPS_VENDU] = pd.to_numeric(df_bo[COL_TEMPS_VENDU], errors="coerce")
    df_bo[COL_TEMPS_PREVU] = pd.to_numeric(df_bo[COL_TEMPS_PREVU], errors="coerce")
    df_bo[COL_TEMPS_CONSO] = pd.to_numeric(df_bo[COL_TEMPS_CONSO], errors="coerce")

    df_bo["Temps_reference"] = df_bo[COL_TEMPS_VENDU].fillna(
        df_bo[COL_TEMPS_PREVU]
    )

    df_bo = df_bo[df_bo["Temps_reference"] > 0]

    # ==================================================
    # MERGE BO + IE (STATUT)
    # ==================================================
    df = df_bo.merge(
        df_ie[[COL_OR, COL_STATUT]],
        on=COL_OR,
        how="left"
    )

    # ==================================================
    # CALCUL EFFICIENCE
    # ==================================================
    df["Efficience"] = df[COL_TEMPS_CONSO] / df["Temps_reference"]

    # ==================================================
    # KPI GLOBAUX
    # ==================================================
    st.subheader("📊 Efficience globale")

    col1, col2, col3 = st.columns(3)

    eff_moy = df["Efficience"].mean()
    pct_ok = (df["Efficience"] <= 1).mean()
    pct_crit = (df["Efficience"] > 1.2).mean()

    col1.metric("Efficience moyenne", f"{eff_moy:.1%}")
    col2.metric("OR dans le temps", f"{pct_ok:.1%}")
    col3.metric("OR dérive >120%", f"{pct_crit:.1%}")

    st.divider()

    # ==================================================
    # EFFICIENCE PAR ÉQUIPE
    # ==================================================
    st.subheader("🏭 Efficience par équipe")

    eff_equipe = (
        df.groupby(COL_EQUIPE)
        .agg(
            efficience=("Efficience", "mean"),
            nb_or=(COL_OR, "count")
        )
        .reset_index()
        .sort_values("efficience", ascending=False)
    )

    st.dataframe(
        eff_equipe.style.format({"efficience": "{:.1%}"})
    )

    # ==================================================
    # TOP / FLOP TECHNICIENS (COACHING)
    # ==================================================
    st.subheader("🧑‍🔧 Top / Flop techniciens (coaching)")

    eff_tech = (
        df.groupby(COL_TECH)
        .agg(
            efficience=("Efficience", "mean"),
            nb_or=(COL_OR, "count")
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

    # ==================================================
    # ENCOURS ACTIONNABLES
    # ==================================================
    st.subheader("🚨 OR en cours – dérives actionnables")

    equipe_sel = st.selectbox(
        "Filtrer par équipe",
        options=sorted(df[COL_EQUIPE].dropna().unique())
    )

    encours = df[
        (df[COL_STATUT] != "Clôturé") &
        (df[COL_EQUIPE] == equipe_sel) &
        (df["Efficience"] > 1)
    ]

    st.dataframe(
        encours[
            [
                COL_OR,
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

