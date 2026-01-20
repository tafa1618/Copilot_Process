import pandas as pd
from datetime import datetime
import unicodedata
from typing import Optional, Tuple

from .llti_preprocess import filter_current_quarter, filter_caterpillar, load_bo_file
from column_validation import validate_required_columns


from column_validation import normalize_column_name


def _simplify(s: str) -> str:
    # Utiliser la même normalisation que validate_required_columns
    return normalize_column_name(s)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    cols = df.columns
    simplified = {c: _simplify(c) for c in cols}
    for cand in candidates:
        sc = _simplify(cand)
        for orig, simp in simplified.items():
            if sc == simp:
                return orig
    # fallback: partial match
    for cand in candidates:
        sc = _simplify(cand)
        for orig, simp in simplified.items():
            if sc in simp or simp in sc:
                return orig
    return None


def _parse_date_series(s: pd.Series, prefer_dayfirst: Optional[bool] = None) -> pd.Series:
    """Parse une Series de dates en testant dayfirst=True et dayfirst=False et
    en retenant la conversion la plus complète.

    Si `prefer_dayfirst` est True/False, on force cette reconstruction (utile si
    on sait qu'un fichier est en format français ou anglais).
    """
    if s is None:
        return s
    if hasattr(s, 'dtype') and (str(s.dtype).startswith('datetime') or s.dtype == 'datetime64[ns]'):
        return s

    # tenter les deux formats
    try:
        parsed_df = pd.to_datetime(s, errors='coerce', dayfirst=True)
    except TypeError:
        parsed_df = pd.to_datetime(s, errors='coerce')
    parsed_en = pd.to_datetime(s, errors='coerce', dayfirst=False)

    if prefer_dayfirst is True:
        return parsed_df
    if prefer_dayfirst is False:
        return parsed_en

    # fallback heuristique: garder celui qui parse le plus de dates
    if parsed_df.notna().sum() >= parsed_en.notna().sum():
        return parsed_df
    return parsed_en


def load_inspect_file(file) -> pd.DataFrame:
    """Charge un fichier d'inspections (Excel ou CSV) en DataFrame."""
    if isinstance(file, str):
        try:
            return pd.read_excel(file)
        except Exception:
            return pd.read_csv(file)
    try:
        return pd.read_excel(file)
    except Exception:
        try:
            file.seek(0)
        except Exception:
            pass
        return pd.read_csv(file)


def load_pointages_file(file) -> pd.DataFrame:
    if file is None:
        return pd.DataFrame()
    if isinstance(file, str):
        return pd.read_excel(file)
    return pd.read_excel(file)


def compute_inspection_rate(
    bo_file,
    inspect_file,
    pointage_file=None,
) -> Tuple[float, pd.DataFrame]:
    """Calcule l'Inspection Rate par facture.

    Logique : pour chaque facture (N° Facture (Lignes)) du BO (filtré pour Caterpillar et trimestre courant) :
     - seules les lignes d'inspection avec un statut "Completed" sont prises en compte.
     - si l'OR de la facture est trouvé dans le fichier `inspect`, la facture est considérée inspectée (méthode 'OR').
     - sinon on regarde les numéros de série présents dans la facture ; si un de ces numéros de série a été inspecté pendant le trimestre courant, la facture est considérée inspectée (méthode 'Serial').
     - sinon la facture est marquée non inspectée.

    Retourne : (inspection_rate (0..1), dataframe détaillé par facture)
    """
    # --- Chargements
    bo = load_bo_file(bo_file)
    inspect = load_inspect_file(inspect_file)
    pointages = load_pointages_file(pointage_file) if pointage_file is not None else pd.DataFrame()

    # --- Filtres et validations
    # Garder uniquement Caterpillar et trimestre courant
    bo = filter_caterpillar(bo)
    bo = filter_current_quarter(bo)

    required_bo_cols = [
        "N° Facture (Lignes)",
        "N° OR (Segment)",
        "Numéro série Equipement (Segment)",
        "Constructeur de l'équipement",
        "Date Facture (Lignes)",
    ]
    try:
        validate_required_columns(bo, required_bo_cols)
    except ValueError as e:
        raise ValueError(f"Problème avec les colonnes du fichier BO : {e}")

    # --- Détecter colonnes utiles dans inspect
    OR_CANDIDATES = [
        "N° OR (Segment)", "N° OR", "OR", "Numéro OR", "N° OR (Lignes)", "N° OR (Or)", "ordre", "Work Order Number", "Work Order No", "Work Order"
    ]
    SERIAL_CANDIDATES = [
        "Numéro série Equipement (Segment)", "Numéro série", "Numéro de série", "numero serie", "serial number", "serial", "S/N", "SN"
    ]
    DATE_CANDIDATES = ["Date inspection", "Date", "date", "Date d'inspection", "Date Controle", "Complete Date (UTC)", "Complete Date"]
    TECH_CANDIDATES = ["Technicien", "Technician", "Intervenant", "Salarié - Nom", "Nom"]
    STATUS_CANDIDATES = ["Status", "Statut", "Status Description"]
    CUSTOMER_CANDIDATES = ["Customer Name", "Customer", "Nom client", "Client"]

    # Valider les colonnes essentielles pour le fichier inspect
    required_inspect_cols = ["Status"]  # Au moins le statut pour filtrer
    try:
        validate_required_columns(inspect, required_inspect_cols)
    except ValueError as e:
        raise ValueError(f"Problème avec les colonnes du fichier Cat Inspect : {e}")

    or_col = _find_column(inspect, OR_CANDIDATES)
    serial_col = _find_column(inspect, SERIAL_CANDIDATES)
    date_col = _find_column(inspect, DATE_CANDIDATES)
    tech_col = _find_column(inspect, TECH_CANDIDATES)
    status_col = _find_column(inspect, STATUS_CANDIDATES)
    customer_col = _find_column(inspect, CUSTOMER_CANDIDATES)

    # --- Normaliser et filtrer : ne garder que les inspections avec statut "Completed"
    if status_col is not None:
        inspect[status_col] = inspect[status_col].astype(str).str.strip()
        # considérer différents libellés courants (en/ fr)
        completed_mask = inspect[status_col].str.lower().str.contains(r"completed|complete|termin[eé]s?|termine|fini|done", regex=True, na=False)
        inspect = inspect[completed_mask]

    # normaliser types
    if or_col is not None:
        inspect[or_col] = inspect[or_col].astype(str).str.strip()
    if serial_col is not None:
        inspect[serial_col] = inspect[serial_col].astype(str).str.strip()
    if date_col is not None:
        # Les dates dans le fichier Cat Inspect sont en format anglais (month/day/year) -> prefer_dayfirst=False
        inspect[date_col] = _parse_date_series(inspect[date_col], prefer_dayfirst=False)

    # --- Préparer set d'OR inspectés (toutes dates)
    inspected_or_set = set()
    if or_col is not None:
        inspected_or_set = set(inspect[or_col].dropna().astype(str).str.strip().unique())

    # --- Préparer série inspectées durant le trimestre courant
    today = datetime.today()
    current_q = (today.month - 1) // 3 + 1
    current_y = today.year

    inspected_serials_q = set()
    if serial_col is not None and date_col is not None:
        tmp = inspect.dropna(subset=[serial_col, date_col]).copy()
        tmp = tmp[(tmp[date_col].dt.year == current_y) & (tmp[date_col].dt.quarter == current_q)]
        inspected_serials_q = set(tmp[serial_col].astype(str).str.strip().unique())

    # --- Préparer pointages recherche : déterminer la colonne OR et technicien dans pointages
    pointage_or_col = None
    possible_or_candidates = OR_CANDIDATES + ["N° OR", "N° OR (Segment)", "OR (Numéro)", "OR Number", "OR"]
    # colonnes spécifiques à récupérer pour le suivi
    POINTAGE_NAME_CANDIDATES = ["Salarié - Nom", "Nom Salarié", "Technicien", "Nom", "Employee Name"]
    POINTAGE_TEAM_CANDIDATES = ["Salarié - Equipe(Nom)", "Equipe", "Team", "Equipe (Nom)", "Team Name", "Equipe Nom"]
    POINTAGE_ORNUM_CANDIDATES = ["OR (Numéro)", "OR Number", "N° OR", "OR", "Order Number"]

    if not pointages.empty:
        pointage_or_col = _find_column(pointages, possible_or_candidates)
        pointage_tech_col = _find_column(pointages, POINTAGE_NAME_CANDIDATES + TECH_CANDIDATES)
        pointage_team_col = _find_column(pointages, POINTAGE_TEAM_CANDIDATES)
        pointage_or_num_col = _find_column(pointages, POINTAGE_ORNUM_CANDIDATES)
    else:
        pointage_tech_col = None
        pointage_team_col = None
        pointage_or_num_col = None

    # --- Agréger par facture
    results = []
    group = bo.groupby("N° Facture (Lignes)")
    for facture, df_fact in group:
        ors = df_fact["N° OR (Segment)"].dropna().astype(str).str.strip().unique().tolist()
        serials = df_fact["Numéro série Equipement (Segment)"].dropna().astype(str).str.strip().unique().tolist()

        inspected = False
        method = None
        inspect_dates = []
        inspectors = []
        customers = []

        # 1) OR match
        for orv in ors:
            if not orv or orv.lower() in ["nan", "none"]:
                continue
            # comparer string-wise
            if orv in inspected_or_set:
                    inspected = True
                    method = "OR"
                    # collect dates, techs & customers if available
                    if or_col is not None and date_col is not None:
                        rows = inspect[inspect[or_col].astype(str).str.strip() == orv]
                        inspect_dates += rows[date_col].dropna().astype(str).tolist()
                        if tech_col is not None:
                            inspectors += rows[tech_col].dropna().astype(str).tolist()
                        if customer_col is not None:
                            customers += rows[customer_col].dropna().astype(str).tolist()
                    break
        # 2) Serial match in quarter
        if not inspected:
            for s in serials:
                if not s or s.lower() in ["nan", "none"]:
                    continue
                if s in inspected_serials_q:
                    inspected = True
                    method = "Serial"
                    if serial_col is not None and date_col is not None:
                        rows = inspect[inspect[serial_col].astype(str).str.strip() == s]
                        # keep only those in current quarter
                        if date_col is not None:
                            rows = rows[(rows[date_col].dt.year == current_y) & (rows[date_col].dt.quarter == current_q)]
                        inspect_dates += rows[date_col].dropna().astype(str).tolist()
                        if tech_col is not None:
                            inspectors += rows[tech_col].dropna().astype(str).tolist()
                        if customer_col is not None:
                            customers += rows[customer_col].dropna().astype(str).tolist()
        # --- Pointages : extraire nom, équipe, OR (numéro) pour suivi
        technicians = []
        pointage_records = []
        if not pointages.empty:
            if pointage_or_col is not None:
                for orv in ors:
                    if not orv or orv.lower() in ["nan", "none"]:
                        continue
                    matched = pointages[pointages[pointage_or_col].astype(str).str.strip() == orv]
                    if not matched.empty:
                        for _, r in matched.iterrows():
                            name = None
                            team = None
                            ornum = None
                            if pointage_tech_col is not None and pointage_tech_col in matched.columns and pd.notna(r.get(pointage_tech_col)):
                                name = str(r.get(pointage_tech_col)).strip()
                            if pointage_team_col is not None and pointage_team_col in matched.columns and pd.notna(r.get(pointage_team_col)):
                                team = str(r.get(pointage_team_col)).strip()
                            if pointage_or_num_col is not None and pointage_or_num_col in matched.columns and pd.notna(r.get(pointage_or_num_col)):
                                ornum = str(r.get(pointage_or_num_col)).strip()
                            else:
                                ornum = orv
                            if name:
                                technicians.append(name)
                            record = "; ".join(x for x in [name, team, f"OR:{ornum}"] if x)
                            pointage_records.append(record)
            else:
                for orv in ors:
                    mask = pointages.apply(lambda row: row.astype(str).str.contains(str(orv), case=False, na=False).any(), axis=1)
                    matched = pointages[mask]
                    if not matched.empty:
                        for _, r in matched.iterrows():
                            name = None
                            team = None
                            ornum = None
                            if pointage_tech_col is not None and pointage_tech_col in matched.columns and pd.notna(r.get(pointage_tech_col)):
                                name = str(r.get(pointage_tech_col)).strip()
                            if pointage_team_col is not None and pointage_team_col in matched.columns and pd.notna(r.get(pointage_team_col)):
                                team = str(r.get(pointage_team_col)).strip()
                            if pointage_or_num_col is not None and pointage_or_num_col in matched.columns and pd.notna(r.get(pointage_or_num_col)):
                                ornum = str(r.get(pointage_or_num_col)).strip()
                            else:
                                ornum = orv
                            if name:
                                technicians.append(name)
                            record = "; ".join(x for x in [name, team, f"OR:{ornum}"] if x)
                            pointage_records.append(record)

        inspectors = list(dict.fromkeys(inspectors))
        technicians = list(dict.fromkeys(technicians))
        pointage_records = list(dict.fromkeys(pointage_records))

        results.append({
            "N° Facture": facture,
            "ORs": ", ".join(ors) if ors else None,
            "Serials": ", ".join(serials) if serials else None,
            "Inspected": int(inspected),
            "Method": method,
            "InspectionDates": ", ".join(inspect_dates) if inspect_dates else None,
            "Inspectors": ", ".join(inspectors) if inspectors else None,
            "Customers": ", ".join(customers) if customers else None,
            "PointageRecords": ", ".join(pointage_records) if pointage_records else None,
            "TechniciansPointed": ", ".join(technicians) if technicians else None,
        })

    df_res = pd.DataFrame(results)

    total = len(df_res)
    inspected_count = int(df_res["Inspected"].sum()) if total > 0 else 0

    rate = inspected_count / total if total > 0 else 0.0

    return rate, df_res
