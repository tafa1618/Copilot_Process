import streamlit as st
from datetime import date

# ===============================
# IMPORT PAGES KPI
# ===============================
from kpis.productivite import page_productivite
from kpis.efficience import page_efficience
from kpis.llti import page_llti


# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="Copilote Méthode & Process – Neemba Sénégal",
    layout="wide"
)

# ===============================
# INIT SESSION STATE
# ===============================
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

if "productivite_globale" not in st.session_state:
    st.session_state.productivite_globale = None

if "productivite_calculee" not in st.session_state:
    st.session_state.productivite_calculee = False


# ===============================
# HEADER GLOBAL
# ===============================
st.title("🧭 Copilote – Méthode & Process | Neemba Sénégal")
st.caption(f"Situation des KPI YTD – au {date.today().strftime('%d/%m/%Y')}")
st.divider()


# ===============================
# PAGE ACCUEIL
# ===============================
if st.session_state.page == "Accueil":

    st.subheader("👋 Bienvenue dans le Copilote Méthode & Process")

    st.markdown(
        """
        Vue synthétique et opérationnelle de l’état des **KPI Méthode & Process**.  
        Les indicateurs se mettent à jour automatiquement dès que les données
        sont chargées dans les modules dédiés.
        """
    )

    st.divider()

    # ===============================
    # RÉSUMÉ KPI
    # ===============================
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.session_state.productivite_calculee:
            st.metric(
                "Productivité YTD",
                f"{st.session_state.productivite_globale:.1%}"
            )
        else:
            st.metric(
                "Productivité YTD",
                "—",
                help="Chargez le fichier de pointages pour calculer la productivité"
            )

        st.metric("Inspection Rate", "—")

    with col2:
        st.metric("Service Response", "—")
        st.metric("PM Accuracy", "—")

    with col3:
        st.metric("CVA Fulfillment", "—")
        st.metric("PIP", "—")

    st.divider()

    # ===============================
    # NAVIGATION KPI
    # ===============================
    st.subheader("🔎 Accéder aux analyses détaillées")

    nav1, nav2, nav3 = st.columns(3)

    with nav1:
        if st.button("📊 Productivité"):
            st.session_state.page = "Productivité"

        if st.button("⚙️ Efficience"):
            st.session_state.page = "Efficience"

    with nav2:
        if st.button("🔍 Inspection Rate"):
            st.session_state.page = "Inspection"

        if st.button("📦 CVA Fulfillment"):
            st.session_state.page = "CVA"

    with nav3:
        if st.button("🛠️ Service Response"):
            st.session_state.page = "Service"

        if st.button("🧪 PIP"):
            st.session_state.page = "PIP"

        if st.button("📉 LLTI"):
            st.session_state.page = "LLTI"


# ===============================
# PAGE PRODUCTIVITÉ
# ===============================
elif st.session_state.page == "Productivité":

    page_productivite()

    st.divider()
    if st.button("⬅️ Retour à l’accueil"):
        st.session_state.page = "Accueil"


# ===============================
# PAGE EFFICIENCE
# ===============================
elif st.session_state.page == "Efficience":

    page_efficience()

    st.divider()
    if st.button("⬅️ Retour à l’accueil"):
        st.session_state.page = "Accueil"


# ===============================
# PAGE LLTI
# ===============================
elif st.session_state.page == "LLTI":

    page_llti()

    st.divider()
    if st.button("⬅️ Retour à l’accueil"):
        st.session_state.page = "Accueil"


# ===============================
# AUTRES PAGES (PLACEHOLDERS)
# ===============================
elif st.session_state.page == "Inspection":
    st.header("🔍 Inspection Rate")
    st.info("Page à implémenter")
    if st.button("⬅️ Retour à l’accueil"):
        st.session_state.page = "Accueil"

elif st.session_state.page == "CVA":
    st.header("📦 CVA Fulfillment")
    st.info("Page à implémenter")
    if st.button("⬅️ Retour à l’accueil"):
        st.session_state.page = "Accueil"

elif st.session_state.page == "Service":
    st.header("🛠️ Service Response")
    st.info("Page à implémenter")
    if st.button("⬅️ Retour à l’accueil"):
        st.session_state.page = "Accueil"

elif st.session_state.page == "PIP":
    st.header("🧪 PIP")
    st.info("Page à implémenter")
    if st.button("⬅️ Retour à l’accueil"):
        st.session_state.page = "Accueil"

