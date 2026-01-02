# kpis/productivite.py

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from preprocessing.productivite_preprocessing import preprocess_productivite
from preprocessing.exhaustivite_preprocessing import compute_exhaustivite


def page_productivite():
    # ==================================================
    # CONFIG
    # ==================================================
    sns.set_theme(style="whitegrid")
    st.header("📊 Productivité & Exhaustivité – Service (hors CRC)")
    st.caption(
        "⚠️ Indicateur à titre **opérationnel** – basé sur l’extraction 3 mois glissants (BI validée)."
    )
    st.divider()

    # ==================================================
    # UPLOAD
    # ==================================================
    uploaded_file = st.file_uploader(
        "Charger l’extraction 3 mois glissants (Pointages Service)",
        type=["xlsx"],
        key="productivite_upload"
    )

    if not uploaded_file:
        st.info("Veuillez charger le fichier d’extraction.")
        return

    df_raw = pd.read_excel(uploaded_file)

    # ==================================================
    # PREPROCESSING
    # ==================================================
    try:
        df = preprocess_productivite(df_raw)
    except Exception as e:
        st.error(f"Erreur preprocessing : {e}")
        return

    if df.empty:
        st.warning("Aucune donnée exploitable.")
        return

    # ==================================================
    # FILTRES
    # ==================================================
    st.subheader("Filtres")

    col1, col2 = st.columns(2)

    with col1:
        equipes = sorted(df["Salarié - Equipe(Nom)"].unique())
        equipes_sel = st.multiselect(
            "Équipes",
            equipes,
            default=equipes
        )

    with col2:
        mois = sorted(df["Mois"].unique())
        mois_sel = st.selectbox(
            "Mois analysé",
            mois,
            index=len(mois) - 1
        )

    df = df[
        (df["Salarié - Equipe(Nom)"].isin(equipes_sel)) &
        (df["Mois"] == mois_sel)
    ]

    if df.empty:
        st.warning("Aucune donnée pour ces filtres.")
        return

    st.divider()

    # ==================================================
    # 1️⃣ EXHAUSTIVITÉ
    # ==================================================
    st.subheader("🗓️ Exhaustivité des pointages")

    exhaustivite = compute_exhaustivite(df)

    data_exh = exhaustivite.get(mois_sel)

    if data_exh:
        techs = list(data_exh["statuts"].keys())

        fig, ax = plt.subplots(
            figsize=(max(10, len(techs) * 0.6), 6)
        )

        # Mapping couleurs
        color_map = {
            "Non conforme": "#d73027",
            "Incomplet": "#fee08b",
            "Conforme": "#1a9850",
            "Surpointage": "#4575b4",
            "Weekend OK": "#f0f0f0",
            "Travail weekend": "#984ea3",
            "": "#ffffff"
        }

        pivot = pd.DataFrame(data_exh["statuts"]).T
        color_df = pivot.applymap(lambda x: color_map.get(x, "#ffffff"))

        ax.imshow(
            color_df.applymap(
                lambda c: plt.colors.to_rgb(c)
                if c != "#ffffff" else (1, 1, 1)
            ).values,
            aspect="auto"
        )

        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)

        ax.set_xlabel("Jour du mois")
        ax.set_ylabel("Techniciens")
        ax.set_title(f"Exhaustivité – {mois_sel}")

        st.pyplot(fig)

    else:
        st.info("Exhaustivité indisponible.")

    st.divider()

    # ==================================================
    # 2️⃣ PRODUCTIVITÉ GLOBALE
    # ==================================================
    total_fact = df["Facturable"].sum()
    total_trav = df["Hr_Totale"].sum()
    prod_globale = total_fact / total_trav if total_trav > 0 else 0

    st.metric("Productivité globale", f"{prod_globale:.1%}")

    # Sauvegarde pour page Accueil
    st.session_state.productivite_globale = prod_globale
    st.session_state.productivite_calculee = True

    st.divider()

    # ==================================================
    # 3️⃣ PRODUCTIVITÉ PAR TECHNICIEN
    # ==================================================
    st.subheader("Productivité par technicien")

    prod_tech = (
        df.groupby("Salarié - Nom")
        .agg(
            Heures=("Hr_Totale", "sum"),
            Facturable=("Facturable", "sum")
        )
        .reset_index()
    )

    prod_tech["Productivité"] = (
        prod_tech["Facturable"] / prod_tech["Heures"]
    )

    prod_tech = prod_tech.sort_values(
        "Productivité", ascending=False
    )

    st.dataframe(
        prod_tech.style.format({
            "Productivité": "{:.1%}",
            "Heures": "{:.1f}",
            "Facturable": "{:.1f}"
        }),
        use_container_width=True
    )

    st.divider()

    # ==================================================
    # 4️⃣ ÉVOLUTION JOURNALIÈRE
    # ==================================================
    st.subheader("Évolution journalière de la productivité")

    prod_jour = (
        df.groupby("Saisie heures - Date")
        .agg(
            Heures=("Hr_Totale", "sum"),
            Facturable=("Facturable", "sum")
        )
        .reset_index()
    )

    prod_jour["Productivité"] = (
        prod_jour["Facturable"] / prod_jour["Heures"]
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(
        data=prod_jour,
        x="Saisie heures - Date",
        y="Productivité",
        marker="o",
        ax=ax
    )

    ax.set_ylabel("Productivité")
    ax.set_xlabel("Date")
    ax.set_title("Tendance journalière – Productivité")

    st.pyplot(fig)
