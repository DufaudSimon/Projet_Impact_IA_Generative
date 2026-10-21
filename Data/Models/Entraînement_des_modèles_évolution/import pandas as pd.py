import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. Configuration initiale
sns.set_theme(style="whitegrid")
fichier_csv = "notable_ai_models.csv"

print(f"Chargement des données depuis {fichier_csv}...")
df = pd.read_csv(fichier_csv)

# 2. Nettoyage et préparation des données
# Adaptation aux noms de colonnes habituels d'Epoch AI
col_date = 'Publication date'
col_compute = 'Training compute (FLOP)'
col_params = 'Parameters'
col_org = 'Organization'
col_domain = 'Domain'

# Conversion de la date en format datetime
df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
df = df.dropna(subset=[col_date]) # On garde que les lignes avec une date valide
df['Year'] = df[col_date].dt.year

# 3. Création de la figure avec 4 sous-graphiques (2x2)
fig, axes = plt.subplots(2, 2, figsize=(18, 12))
fig.suptitle("Analyse des modèles d'IA notables (Epoch AI)", fontsize=18, fontweight='bold', y=0.98)

# --- Graphique 1 : Évolution du calcul d'entraînement (FLOP) dans le temps ---
ax1 = axes[0, 0]
sns.scatterplot(data=df, x=col_date, y=col_compute, hue=col_domain, alpha=0.7, ax=ax1)
ax1.set_yscale('log')
ax1.set_title('Évolution du calcul d\'entraînement (FLOP)', fontsize=14)
ax1.set_xlabel('Date de publication')
ax1.set_ylabel('Training Compute (FLOP) - Échelle Log')
ax1.legend(title='Domaine', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')

# --- Graphique 2 : Évolution du nombre de paramètres ---
ax2 = axes[0, 1]
if col_params in df.columns:
    df_params = df.dropna(subset=[col_params])
    sns.scatterplot(data=df_params, x=col_date, y=col_params, color='coral', alpha=0.7, ax=ax2)
    ax2.set_yscale('log')
    ax2.set_title('Évolution du nombre de paramètres', fontsize=14)
    ax2.set_xlabel('Date de publication')
    ax2.set_ylabel('Paramètres - Échelle Log')
else:
    ax2.text(0.5, 0.5, 'Données de paramètres non trouvées', ha='center')

# --- Graphique 3 : Nombre de modèles publiés par année ---
ax3 = axes[1, 0]
models_per_year = df['Year'].value_counts().sort_index()
models_per_year = models_per_year[models_per_year.index >= 2010] # Focus sur l'ère du Deep Learning
sns.barplot(x=models_per_year.index.astype(int), y=models_per_year.values, color='skyblue', ax=ax3)
ax3.set_title('Nombre de modèles notables publiés par année (depuis 2010)', fontsize=14)
ax3.set_xlabel('Année')
ax3.set_ylabel('Nombre de modèles')
ax3.tick_params(axis='x', rotation=45)

# --- Graphique 4 : Top 10 des organisations ayant publié le plus de modèles ---
ax4 = axes[1, 1]
if col_org in df.columns:
    # Gérer les modèles avec plusieurs organisations (séparées par des virgules)
    orgs = df[col_org].dropna().str.split(',').explode().str.strip()
    top_orgs = orgs.value_counts().head(10)
    sns.barplot(y=top_orgs.index, x=top_orgs.values, palette='viridis', ax=ax4)
    ax4.set_title('Top 10 des organisations (nombre de modèles notables)', fontsize=14)
    ax4.set_xlabel('Nombre de modèles')
    ax4.set_ylabel('Organisation')
else:
    ax4.text(0.5, 0.5, 'Données d\'organisation non trouvées', ha='center')

# Ajustement de la mise en page
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# Sauvegarde et affichage
fichier_sortie = "analyse_ai_models.png"
plt.savefig(fichier_sortie, dpi=300, bbox_inches='tight')
print(f"Graphiques générés et sauvegardés sous le nom : {fichier_sortie}")
plt.show()