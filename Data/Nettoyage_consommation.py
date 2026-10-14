# ============================================================
# 1. IMPORTATION DES BIBLIOTHÈQUES
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# 2. CHARGEMENT DU FICHIER CSV
# ============================================================

fichier = "Data/consommation-annuelle-par-iris.csv"

df = pd.read_csv(
    fichier,
    sep=None,
    engine="python",
    encoding="utf-8-sig"
)

print("Fichier chargé avec succès.")
print(f"Nombre de lignes : {df.shape[0]:,}")
print(f"Nombre de colonnes : {df.shape[1]}")


# Dimensions et structure générale
print("DIMENSIONS :", df.shape)

print("\nNOMS DES COLONNES :")
print(df.columns.tolist())

print("\nTYPES DES VARIABLES :")
df.info()

print("\nAPERÇU DES DONNÉES :")

print("\nEXEMPLES DE VALEURS PAR COLONNE :")
for colonne in df.columns:
    print(f"\n{colonne}")
    print(df[colonne].dropna().head(5).tolist())

