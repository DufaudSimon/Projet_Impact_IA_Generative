"""
Nettoyage de comparIA-votes : parquet -> CSV allégé
====================================================
Lit le fichier .parquet en ne chargeant QUE les colonnes utiles (les colonnes
lourdes conversation_a / conversation_b ne sont jamais lues), puis écrit un CSV.

Dépendances : pip install pandas pyarrow   (polars / duckdb en secours)
Usage       : python nettoyage_comparia_votes.py
"""

from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------
PARQUET_PATH = "votes.parquet"   # <- chemin vers votre fichier .parquet
CSV_PATH = "comparia_votes_clean.csv"     # <- fichier CSV de sortie

QUALIFIERS = [
    "useful",
    "creative",
    "clear_formatting",
    "incorrect",
    "superficial",
    "instructions_not_followed",
]

COLONNES = (
    ["timestamp", "model_a_name", "model_b_name", "chosen_model_name"]
    + [f"conv_{q}_{side}" for q in QUALIFIERS for side in ("a", "b")]
    + ["conv_turns", "system_prompt_a", "system_prompt_b"]
)


# --------------------------------------------------------------------------
# CHARGEMENT (uniquement les colonnes utiles, avec lecteurs de secours)
# --------------------------------------------------------------------------
def charger_parquet(path: str, colonnes: list[str]) -> pd.DataFrame:
    # 1) pandas / pyarrow
    try:
        return pd.read_parquet(path, columns=colonnes)
    except Exception as e:
        print(f"pyarrow a échoué ({e})\n-> essai avec polars")

    # 2) polars
    try:
        import polars as pl

        return pl.read_parquet(path, columns=colonnes).to_pandas()
    except Exception as e:
        print(f"polars a échoué ({e})\n-> essai avec duckdb")

    # 3) duckdb
    import duckdb

    cols_sql = ", ".join(f'"{c}"' for c in colonnes)
    return duckdb.sql(
        f"SELECT {cols_sql} FROM read_parquet('{Path(path).as_posix()}')"
    ).df()


if not Path(PARQUET_PATH).exists():
    raise FileNotFoundError(
        f"Fichier introuvable : {PARQUET_PATH}\n"
        "Modifiez PARQUET_PATH en haut du script (chemin complet si besoin)."
    )

df = charger_parquet(PARQUET_PATH, COLONNES)

# Garde-fou : colonnes demandées mais absentes du fichier
manquantes = [c for c in COLONNES if c not in df.columns]
if manquantes:
    print(f"Attention, colonnes absentes : {manquantes}")

df = df[[c for c in COLONNES if c in df.columns]]

# --------------------------------------------------------------------------
# NETTOYAGE LÉGER
# --------------------------------------------------------------------------
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
df = df.sort_values("timestamp").reset_index(drop=True)

# --------------------------------------------------------------------------
# EXPORT CSV
# --------------------------------------------------------------------------
# utf-8-sig : le CSV s'ouvre correctement (accents) dans Excel sous Windows
df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

print(f"\nFichier écrit : {Path(CSV_PATH).resolve()}")
print(f"Lignes   : {len(df):,}")
print(f"Colonnes : {df.shape[1]}")
print(f"Taille   : {Path(CSV_PATH).stat().st_size / 1e6:,.1f} Mo")
print("\nValeurs vides par colonne (chosen_model_name vide = égalité ; "
      "system_prompt vide = pas de consigne) :")
print(df.isna().sum()[lambda s: s > 0].to_string())
print("\nAperçu :")
print(df.head(3).to_string())