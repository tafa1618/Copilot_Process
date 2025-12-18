import streamlit as st
from datetime import date
from kpis.productivite import page_productivite

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(
    page_title="Copilote Méthode & Process – Neemba Sénégal",
    layout="wide"
)

# ==================================================
# INIT NAVIGATION
# ==================================================
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

# ==================================================
# HEADER GLOBAL
# ==================================================
st.title("🧭 Copilote – Méthode & Process | Neemba Sénégal")
st.divider()

# ==================================================
# PAGE ACCUEIL
# ==================================================
if st.session_state.page == "Accueil":

    st.subheader("👋 Bienvenue dans le Copilote Méthode & Process")

    st.markdown(
        """
        Vue synthétique de l’état des **KPI opérationnels**.
        Cliquez sur un KPI pour accéder à l’analyse détaillée.
        """
    )

    st.divider()

    # ---- NAVIGATION KPI ----
    nav1, nav2, nav3 = st.columns(3)

    with nav1:
        if st.button("📊 Productivité"):
            st.session_state.page = "Productivité"

    with nav2:
        if st.button("⚙️ Efficience"):
            st.session_state.page = "Efficience"

    with nav3:
        if st.button("🔍 Inspection Rate"):
            st.session_state.page = "Inspection"

# ==================================================
# PAGE PRODUCTIVITÉ
# ==================================================
elif st.session_state.page == "Productivité":

    page_productivite()

    st.divider()
    if st.button("⬅️ Retour à l’accueil"):
        st.session_state.page = "Accueil"

# ==================================================
# PAGE EFFICIENCE (placeholder)
# ==================================================
elif st.session_state.page == "Efficience":

    st.header("⚙️ Efficience – OR")
    st.info("Page Efficience à implémenter")

    st.divider()
    if st.button("⬅️ Retour à l’accueil"):
        st.session_state.page = "Accueil"

# ==================================================
# PAGE INSPECTION (placeholder)
# ==================================================
elif st.session_state.page == "Inspection":

    st.header("🔍 Inspection Rate")
    st.info("Page Inspection à implémenter")

    st.divider()
    if st.button("⬅️ Retour à l’accueil"):
        st.session_state.page = "Accueil"
