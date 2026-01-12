import streamlit as st
import pandas as pd
from datetime import datetime

from preprocessing.llti_preprocess import preprocess_llti


@st.cache_data(show_spinner="Chargement des données LLTI...")
def load_llti(file):
    return preprocess_llti(file)


def _llti_color(score: float):
    """Retourne (label, hex) selon le score en jours."""
    if pd.isna(score):
        return "—", "#808080"
    if score <= 7:
        return "Vert (≤7j)", "#2ca02c"
    if score <= 12:
        return "Orange (≤12j)", "#ff7f0e"
    if score <= 17:
        return "Jaune (≤17j)", "#d0a000"
    return "Rouge (>17j)", "#d62728"


def page_llti():
    st.header("📉 LLTI – Lagging Invoicing (Quartile)")

    uploaded = st.file_uploader(
        "Charger le fichier Business Object (BO) (Excel)",
        type=["xlsx"],
        key="llti_bo"
    )

    if not uploaded:
        st.info("Veuillez charger le fichier BO pour calculer le KPI LLTI.")
        return

    try:
        df = load_llti(uploaded)
    except ValueError as e:
        st.error(str(e))
        return

    if df.empty:
        st.warning("Aucune ligne Caterpillar trouvée pour le trimestre courant.")
        return

    # --- Calcul en se focalisant sur la facture la plus récente par OR ---
    # Dates déjà en datetime dans le pipeline, mais on s'assure
    df["Date Facture (Lignes)"] = pd.to_datetime(df["Date Facture (Lignes)"], errors="coerce")
    df["Pointage dernière date (Segment)"] = pd.to_datetime(df["Pointage dernière date (Segment)"], errors="coerce")

    # Pour chaque OR : ligne de la facture la plus récente
    idx_latest_inv = df.groupby("N° OR (Segment)")["Date Facture (Lignes)"].idxmax()
    latest_invoices = df.loc[idx_latest_inv, ["N° OR (Segment)", "N° Facture (Lignes)", "Date Facture (Lignes)", "Nom Client OR (or)"]].copy()
    latest_invoices = latest_invoices.rename(columns={
        "N° Facture (Lignes)": "Last_invoice_number",
        "Date Facture (Lignes)": "Last_invoice_date"
    })

    # Pour chaque OR : pointage le plus récent (peut être différent de la ligne de facture)
    last_pointages = (
        df
        .groupby("N° OR (Segment)", as_index=False)["Pointage dernière date (Segment)"].max()
        .rename(columns={"Pointage dernière date (Segment)": "Last_pointage_date"})
    )

    per_or = latest_invoices.merge(last_pointages, on="N° OR (Segment)", how="left")

    # Calcul Days_diff = Last_invoice_date - Last_pointage_date (en jours)
    per_or["Days_diff"] = (per_or["Last_invoice_date"] - per_or["Last_pointage_date"]).dt.days

    # Score global : moyenne des Days_diff (une valeur par OR)
    global_score = per_or["Days_diff"].mean()

    # Affichage score avec code couleur
    label, color = _llti_color(global_score)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("LLTI (moyenne en jours)", f"{global_score:.1f} jours")
    with col2:
        st.markdown(
            f"<div style='padding:10px;border-radius:6px;background:{color};color:#ffffff;display:inline-block'>{label}</div>",
            unsafe_allow_html=True
        )

    st.divider()

    # Tableau des facturations à la traîne — basé sur la facture la plus récente par OR
    st.subheader("Facturations à la traîne")

    # Nombre de factures par OR (pour information)
    n_inv = df.groupby("N° OR (Segment)", as_index=False)["N° Facture (Lignes)"].nunique().rename(columns={"N° Facture (Lignes)": "n_invoices"})

    or_summary = (
        per_or
        .merge(n_inv, on="N° OR (Segment)", how="left")
        .rename(columns={
            "Last_invoice_date": "last_facture",
            "Last_pointage_date": "last_pointage",
            "Last_invoice_number": "N° Facture (Lignes)",
            "Days_diff": "Days_diff"
        })
        .sort_values("Days_diff", ascending=False)
    )

    st.dataframe(
        or_summary.head(20).assign(
            Days_diff=lambda d: d["Days_diff"].astype(float).round(1),
            n_invoices=lambda d: d["n_invoices"].fillna(0).astype(int)
        ),
        use_container_width=True
    )

    st.info(
        "Les lignes ci-dessus montrent, pour chaque OR, la facture la plus récente et le nombre total de factures."
    )

    # Détails : liste des factures (triées) pour investigation
    with st.expander("Voir les factures détaillées (triées par écart)"):
        st.dataframe(
            df.assign(Days_diff=lambda d: (d["Date Facture (Lignes)"] - d["Pointage dernière date (Segment)"]).dt.days)
            .sort_values("Days_diff", ascending=False).head(200),
            use_container_width=True
        )

    # =============================
    # SIMULATEUR D'ACTIONS LLTI
    # (adaptation Streamlit du widget ipywidgets fourni)
    # =============================
    st.subheader("Simulateur d'actions LLTI")

    def calculer_n2(n1: int, m1: float, m2: float, objectif: float):
        try:
            numerateur = n1 * (m1 - objectif)
            denominateur = objectif - m2
            if denominateur <= 0:
                return None
            return int(numerateur / denominateur) + 1
        except Exception:
            return None

    # Valeurs par défaut basées sur les données chargées
    default_n1 = int(len(per_or)) if 'per_or' in locals() else 100
    default_m1 = float(global_score) if (not pd.isna(global_score)) else 22.0

    col_a, col_b = st.columns(2)
    with col_a:
        n1 = st.slider("OR clôturés (n1)", min_value=1, max_value=2000, step=1, value=max(10, default_n1))
        m1 = st.slider("LLTI actuel (m1, jours)", min_value=1.0, max_value=100.0, step=0.5, value=round(default_m1,1))
    with col_b:
        objectif = st.slider("LLTI objectif (jours)", min_value=1.0, max_value=100.0, step=0.5, value=7.0)
        m2 = st.slider("LLTI des nouveaux OR (m2, jours)", min_value=0.0, max_value=100.0, step=0.5, value=4.0)

    # Calcul
    n2 = calculer_n2(n1, m1, m2, objectif)

    if n2 is not None:
        st.success(
            f"✅ Pour atteindre un LLTI de **{objectif} jours**, il faut clôturer **{n2} nouveaux OR** avec un LLTI de **{m2} jours**."
        )
    else:
        st.error(
            "❌ Erreur : les paramètres ne permettent pas d’atteindre l’objectif (LLTI trop élevé ou objectif irréaliste)."
        )

    st.divider()

    # Option export CSV
    csv = or_summary.to_csv(index=False)
    st.download_button("Télécharger le tableau (CSV)", csv, file_name="llti_facturations_a_la_traine.csv")