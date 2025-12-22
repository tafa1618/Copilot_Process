def page_efficience():

    st.header("⚙️ Efficience des OR – Pilotage opérationnel")

    st.warning(
        "⚠️ **Lecture indicative**\n\n"
        "Les indicateurs d’efficience sont issus d’un rapprochement multi-sources "
        "(ERP, BO, Pointages) consolidé via Power Query.\n\n"
        "👉 Outil de **pilotage et de coaching**, pas d’évaluation contractuelle."
    )

    st.divider()

    # ===============================
    # UPLOAD UNIQUE
    # ===============================
    uploaded_file = st.file_uploader(
        "Charger le fichier Efficience consolidée (Power Query)",
        type=["xlsx"],
        key="efficience_upload"
    )

    if not uploaded_file:
        st.info("Veuillez charger le fichier d’efficience consolidée.")
        return

    df = pd.read_excel(uploaded_file)

    # ===============================
    # FILTRES GLOBAUX
    # ===============================
    st.subheader("Périmètre d’analyse")

    col1, col2, col3 = st.columns(3)

    with col1:
        equipes = sorted(df["Equipe"].dropna().unique())
        equipe_sel = st.multiselect("Équipe", equipes, default=equipes)

    with col2:
        positions = sorted(df["Position"].dropna().unique())
        position_sel = st.multiselect("Statut OR", positions, default=positions)

    with col3:
        types_or = sorted(df["Type OR"].dropna().unique())
        type_or_sel = st.multiselect("Type OR", types_or, default=types_or)

    # Application filtres
    df_f = df.copy()

    if equipe_sel:
        df_f = df_f[df_f["Equipe"].isin(equipe_sel)]
    if position_sel:
        df_f = df_f[df_f["Position"].isin(position_sel)]
    if type_or_sel:
        df_f = df_f[df_f["Type OR"].isin(type_or_sel)]

    st.divider()

    # ===============================
    # KPI GLOBAUX
    # ===============================
    st.subheader("Indicateurs globaux")

    df_eff = df_f[df_f["Efficience_OR"].notna()]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Efficience moyenne",
            f"{df_eff['Efficience_OR'].mean():.2f}"
        )

    with col2:
        st.metric(
            "OR exploitables",
            f"{len(df_eff)} / {len(df_f)}"
        )

    with col3:
        part_encours = (
            len(df_f[df_f["Position"] == "EC"]) / len(df_f)
            if len(df_f) > 0 else 0
        )
        st.metric(
            "Part OR encours",
            f"{part_encours:.1%}"
        )

    st.divider()

    # ===============================
    # ENCOURS ACTIONNABLE
    # ===============================
    st.subheader("🎯 OR encours – Actions prioritaires")

    encours = df_eff[df_eff["Position"] == "EC"]

    st.dataframe(
        encours[
            [
                "OR",
                "Nom Client OR (or)",
                "Equipe",
                "Technicien",
                "Temps_reference",
                "Temps_consomé_BO",
                "Efficience_OR",
                "Planifié ?"
            ]
        ]
        .sort_values("Efficience_OR")
        .style.format({"Efficience_OR": "{:.2f}"})
    )
