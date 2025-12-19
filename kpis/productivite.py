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
