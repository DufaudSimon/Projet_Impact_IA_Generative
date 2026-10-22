# Sources — Page 1 « Comprendre »

Chaque chiffre ou graphique de la page 1 est listé ci-dessous avec sa source.
Les références [1] à [4] sont les mêmes que dans l'application (`REFS` dans `app.py`).

## Références

| N° | Source | Lien |
|----|--------|------|
| [1] | IEA, « Energy and AI » (communiqué, 10 avril 2025) | https://www.iea.org/news/ai-is-set-to-drive-surging-electricity-demand-from-data-centres-while-offering-the-potential-to-transform-how-the-energy-sector-works |
| [2] | Scientific American, « Data Centers Will Use Twice as Much Energy by 2030 » (analyse du rapport IEA) | https://scientificamerican.com/article/ai-will-drive-doubling-of-data-center-energy-demand-by-2030 |
| [3] | Data Center Dynamics, mesure Google de la requête médiane Gemini (2025) | https://www.datacenterdynamics.com/en/news/google-median-gemini-prompt-uses-024-watt-hours-of-power-and-consumes-026ml-of-water/ |
| [4] | Mistral AI, « Our contribution to a global environmental standard for AI » (2025) | https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai |

## Chiffres et graphiques

| Élément de la page | Valeur | Source | Remarque |
|--------------------|--------|--------|----------|
| KPI « 415 → 945 TWh » et graphique en barres | 415 TWh (2024) ; ≈ 945 TWh (2030) | [1], [2] | 2030 = projection du scénario de base de l'IEA. « Plus de deux fois » et « ≈ consommation du Japon » viennent de [1]. |
| KPI « ×4 » | Demande des datacenters optimisés IA : « plus que quadruple » d'ici 2030 | [1] | Projection, pas une mesure. |
| Graphique en anneau (15 %) | Serveurs IA = 15 % de l'énergie totale des datacenters en 2024 (24 % de l'énergie des serveurs) | [2] | Les 85 % restants sont le complément calculé. |
| KPI « ×38 » (CO₂) | 0,03 g CO₂e par requête médiane Gemini [3] ; 1,14 g CO₂e par réponse de 400 tokens (Le Chat) [4] | [3], [4] | **Calcul maison** : 1,14 ÷ 0,03 = 38. Périmètres différents (voir ci-dessous) : à lire comme un ordre de grandeur de l'écart entre déclarations, pas comme un écart réel entre deux modèles. |
| KPI « ×170 » (eau) | 0,26 mL par requête médiane Gemini [3] ; 45 mL par réponse de 400 tokens [4] | [3], [4] | **Calcul maison** : 45 ÷ 0,26 ≈ 173, arrondi à ×170 dans le texte. Même réserve de périmètre. |

## Pourquoi les chiffres [3] et [4] ne sont pas comparables

- **Google [3]** : chaîne de service uniquement ; exclut l'entraînement, l'énergie du réseau et des terminaux, et le stockage. L'eau comptée est celle du refroidissement direct (l'eau consommée par les centrales électriques n'est pas incluse).
- **Mistral [4]** : analyse de cycle de vie incluant les impacts de fabrication du matériel (estimés, faute d'inventaire fiable des GPU, selon Mistral). Usage « Le Chat », réponse de 400 tokens, hors terminaux des utilisateurs.

## Contenu non chiffré

Les définitions (IA, IA générative, données / entraînement / inférence) et les quatre objectifs du parcours sont des explications générales rédigées pour ce projet, sans chiffre ni source à citer.

## À faire avant publication

- Vérifier les valeurs directement dans les documents primaires lorsque c'est possible : la source [2] relaie le rapport IEA, la source [3] relaie le papier technique de Google.
- Les liens ont été consultés en octobre 2026.
