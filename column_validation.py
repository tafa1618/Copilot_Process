import pandas as pd
import unicodedata
import re
from difflib import SequenceMatcher
from typing import List, Tuple, Optional


def normalize_column_name(name: str) -> str:
    """
    Normalise un nom de colonne selon les règles spécifiées :
    - Suppression des espaces en début/fin
    - Remplacement des espaces multiples par un seul
    - Suppression des caractères invisibles Unicode (NBSP, zero-width, etc.)
    - Normalisation Unicode (NFKD)
    - Suppression des accents
    - Conversion en minuscules
    - Remplacement des tirets et parenthèses par des espaces
    """
    # Suppression des espaces en début/fin
    name = name.strip()
    
    # Remplacement des espaces multiples par un seul
    name = re.sub(r'\s+', ' ', name)
    
    # Suppression des caractères invisibles (non printables, sauf espaces et tabulations)
    name = ''.join(c for c in name if c.isprintable() or c in ' \t\n\r')
    
    # Normalisation Unicode NFKD
    name = unicodedata.normalize('NFKD', name)
    
    # Suppression des accents (caractères de combinaison)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    
    # Conversion en minuscules
    name = name.lower()
    
    # Remplacement des tirets et parenthèses par des espaces
    name = re.sub(r'[-()]', ' ', name)
    
    # Nettoyage final des espaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def find_best_match(target: str, candidates: List[str]) -> Optional[str]:
    """
    Trouve la meilleure correspondance floue pour une chaîne cible parmi des candidats.
    Utilise SequenceMatcher avec un seuil de 0.8 pour considérer une correspondance valide.
    """
    best_match = None
    best_score = 0.0
    
    for candidate in candidates:
        score = SequenceMatcher(None, target, candidate).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate
    
    # Seuil arbitraire pour considérer une correspondance
    if best_score >= 0.8:
        return best_match
    return None


def validate_required_columns(df: pd.DataFrame, required_columns: List[str]) -> None:
    """
    Valide la présence de colonnes obligatoires dans un DataFrame en utilisant une normalisation
    des noms de colonnes et une comparaison floue en cas de non-correspondance exacte.
    
    Args:
        df (pd.DataFrame): Le DataFrame à valider.
        required_columns (List[str]): Liste des noms de colonnes obligatoires.
    
    Raises:
        ValueError: Si une ou plusieurs colonnes obligatoires sont manquantes,
                    avec des détails sur les colonnes attendues, trouvées et suggestions.
    """
    # Normalisation des colonnes du DataFrame
    normalized_df_cols = [normalize_column_name(col) for col in df.columns]
    
    # Normalisation des colonnes attendues
    normalized_required = [normalize_column_name(col) for col in required_columns]
    
    # Mappings pour retrouver les noms originaux
    df_col_map = dict(zip(normalized_df_cols, df.columns))
    required_map = dict(zip(normalized_required, required_columns))
    
    # Liste des colonnes manquantes avec suggestions
    missing_details: List[Tuple[str, Optional[str]]] = []
    
    for norm_req, orig_req in zip(normalized_required, required_columns):
        if norm_req not in normalized_df_cols:
            # Recherche de la meilleure correspondance floue
            best_match_norm = find_best_match(norm_req, normalized_df_cols)
            if best_match_norm:
                best_match_orig = df_col_map[best_match_norm]
                missing_details.append((orig_req, best_match_orig))
            else:
                missing_details.append((orig_req, None))
    
    if missing_details:
        # Construction du message d'erreur détaillé
        error_messages = []
        for expected, suggested in missing_details:
            if suggested:
                error_messages.append(f"Colonne attendue : '{expected}' - Suggestion : '{suggested}'")
            else:
                error_messages.append(f"Colonne attendue : '{expected}' - Aucune suggestion trouvée")
        
        all_found = ", ".join(f"'{col}'" for col in df.columns)
        error_messages.append(f"Colonnes trouvées dans le DataFrame : {all_found}")
        
        raise ValueError("Colonnes obligatoires manquantes :\n" + "\n".join(error_messages))
    
    # Validation silencieuse si tout est OK