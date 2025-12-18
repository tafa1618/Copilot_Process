import streamlit as st
from datetime import date

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="Copilote Méthode & Process – Neemba Sénégal",
    layout="wide"
)

# ===============================
# INIT NAVIGATION
# ===============================
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

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
        Ce copilote fournit une **vue synthétique et actionnable**
        de l’état de nos principaux **KPI opérationnels**.
        """
    )

    # ===============================
    # RÉSUMÉ KPI (placeholder valeurs)
    # ===============================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Productivité YTD", "77 %", delta="+2 %")
        st.metric("Inspection Rate", "67.8 %", delta="-1.2 %")

    with col2:
        st.metric("Service Response", "85.3 %", delta="+0.8 %")
        st.metric("PM Accuracy", "96 %", delta="+1 %")

    with col3:
        st.metric("CVA Fulfillment", "83.8 %", delta="+3 %")
        st.metric("PIP", "9 / 9", delta="Stable")

    st.divider()

    # ===============================
    # BOUTONS DE NAVIGATION
    # ===============================
    st.subheader("🔎 Voir le détail par KPI")

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

# ===============================
# PAGES KPI (PLACEHOLDERS)
# ===============================
elif st.session_state.page == "Productivité":
    st.header("📊 Détail – Productivité")
    st.button("⬅️ Retour à l’accueil", on_click=lambda: st.session_state.update(page="Accueil"))

elif st.session_state.page == "Efficience":
    st.header("⚙️ Détail – Efficience OR")
    st.button("⬅️ Retour à l’accueil", on_click=lambda: st.session_state.update(page="Accueil"))

elif st.session_state.page == "Inspection":
    st.header("🔍 Détail – Inspection Rate")
    st.button("⬅️ Retour à l’accueil", on_click=lambda: st.session_state.update(page="Accueil"))

elif st.session_state.page == "CVA":
    st.header("📦 Détail – CVA Fulfillment")
    st.button("⬅️ Retour à l’accueil", on_click=lambda: st.session_state.update(page="Accueil"))

elif st.session_state.page == "Service":
    st.header("🛠️ Détail – Service Response")
    st.button("⬅️ Retour à l’accueil", on_click=lambda: st.session_state.update(page="Accueil"))

elif st.session_state.page == "PIP":
    st.header("🧪 Détail – PIP")
    st.button("⬅️ Retour à l’accueil", on_click=lambda: st.session_state.update(page="Accueil"))
