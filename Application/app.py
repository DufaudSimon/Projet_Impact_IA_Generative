"""
Dans la peau d'une requête — IA générative & environnement.

Problématique : face à l'opacité du secteur de l'IA générative sur son impact
environnemental, comment mobiliser les données existantes pour éclairer le débat
public et permettre des choix avisés ?

Lancer :  pip install -r requirements.txt  &&  python app.py
Puis ouvrir http://127.0.0.1:8050

Pour l'instant seule la page 1 (« Comprendre ») est rédigée ; les 5 autres
onglets existent (navigation, barre de progression) avec une page d'attente.
Toutes les valeurs chiffrées sont référencées [1], [2]… et listées dans SOURCES.md.
"""

import base64
import os
import threading
import webbrowser

from dash import Dash, html, dcc, Input, Output, callback
import plotly.graph_objects as go

# --------------------------------------------------------------------------- #
# 1. NAVIGATION
# --------------------------------------------------------------------------- #
NAV = [
    ("/", "Comprendre"),
    ("/evolution", "Évolution"),
    ("/infrastructures", "Infrastructures"),
    ("/requete", "La requête"),
    ("/calculateur", "Calculateur"),
    ("/agir", "Agir"),
]

# --------------------------------------------------------------------------- #
# 2. SOURCES (numérotation utilisée dans l'interface et dans SOURCES.md)
# --------------------------------------------------------------------------- #
REFS = {
    1: ("Microsoft AI Economy Institute, « The continued state of global AI diffusion in 2026 » (T2 2026, 21 sept. 2026)",
        "https://blogs.microsoft.com/on-the-issues/2026/09/21/the-continued-state-of-global-ai-diffusion-in-2026/"),
    2: ("Microsoft AI Economy Institute, « Global AI Adoption in 2025 — A Widening Digital Divide » (S2 2025, janv. 2026)",
        "https://www.microsoft.com/en-us/research/wp-content/uploads/2026/01/Microsoft-AI-Diffusion-Report-2025-H2.pdf"),
    3: ("Microsoft, « The state of global AI diffusion in 2026 » (T1 2026, 7 mai 2026)",
        "https://blogs.microsoft.com/on-the-issues/2026/05/07/the-state-of-global-ai-diffusion-in-2026/"),
    4: ("OCDE, « AI use by individuals surges across the OECD as adoption by firms continues to expand » (janv. 2026)",
        "https://www.oecd.org/en/about/news/announcements/2026/01/ai-use-by-individuals-surges-across-the-oecd-as-adoption-by-firms-continues-to-expand.html"),
    5: ("Arcep / CREDOC, « Baromètre du numérique, édition 2026 » (enquête de juin 2025, population de 12 ans et plus)",
        "https://www.arcep.fr/cartes-et-donnees/nos-publications-chiffrees/barometre-du-numerique/le-barometre-du-numerique-edition-2026.html"),
    6: ("Eurostat, « Use of artificial intelligence in enterprises » (Statistics Explained, données extraites en déc. 2025 ; base isoc_eb_ai)",
        "https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Use_of_artificial_intelligence_in_enterprises"),
    7: ("Insee Première, « Les technologies de l'information et de la communication dans les entreprises en 2025 »",
        "https://www.insee.fr/fr/statistiques/9025878"),
    8: ("Stanford HAI, « AI Index Report 2026 », chapitre 4 « Economy » (avril 2026)",
        "https://hai.stanford.edu/assets/files/ai_index_report_2026_chapter_4_economy.pdf"),
    9: ("IEA, « Energy and AI » (communiqué, avril 2025)",
        "https://www.iea.org/news/ai-is-set-to-drive-surging-electricity-demand-from-data-centres-while-offering-the-potential-to-transform-how-the-energy-sector-works"),
}

# Sources de l'ancienne version de la page 1, à renuméroter quand les pages « La requête » et « Calculateur » seront rédigées
REFS_PAGES_SUIVANTES = {
    "Google": ("Data Center Dynamics, « Google: median Gemini prompt uses 0.24 watt-hours… » (méthodologie Google, 2025)",
               "https://www.datacenterdynamics.com/en/news/google-median-gemini-prompt-uses-024-watt-hours-of-power-and-consumes-026ml-of-water/"),
    "Mistral": ("Mistral AI, « Our contribution to a global environmental standard for AI » (analyse de cycle de vie, 2025)",
                "https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai"),
}

# Valeurs affichées -> toutes issues des sources ci-dessus (numéro entre crochets)
# Part de la population de 15 à 64 ans utilisant l'IA générative (%), télémétrie Microsoft [1][2][3]
WORLD_PERIODS = ["S1 2025", "S2 2025", "T1 2026", "T2 2026"]
WORLD = {
    "Monde":        [15.1, 16.3, 17.8, 18.8],
    "Pays du Nord": [22.9, 24.7, 27.5, 28.8],
    "Pays du Sud":  [13.1, 14.1, 15.4, 16.2],
}
FR_MICROSOFT = 44.0     # % France, S2 2025, données Microsoft reprises par Stanford [8]
FR_ARCEP = 48           # % population française de 12 ans et plus, enquête juin 2025 [5]
# Entreprises de 10 personnes ou plus utilisant au moins une technologie d'IA (%)
EU_FIRMS = {2023: 8.1, 2024: 13.5, 2025: 20.0}   # Eurostat [6] (2025 : 19,95 % avant arrondi)
FR_FIRMS = {2023: 6, 2024: 10, 2025: 18}         # Insee [7], arrondis à l'unité
EU_SIZE = {"10 à 49 salariés": 17.0, "50 à 249": 30.4, "250 ou plus": 55.0}   # UE 2025 [6]
# Investissement mondial des entreprises dans l'IA, en milliards de dollars [8]
INVEST_YEARS = list(range(2013, 2026))
INVEST_BN = [14.57, 19.04, 25.43, 33.82, 53.72, 79.62, 103.27, 221.87,
             360.73, 253.25, 201.0, 253.02, 581.69]
DC_2024_TWH = 415       # [9]
DC_2030_TWH = 945       # [9]
# Pour les pages suivantes (non affichées sur la page 1)
CO2_GOOGLE_G = 0.03     # g CO2e / requête médiane Gemini
CO2_MISTRAL_G = 1.14    # g CO2e / réponse de 400 tokens
WATER_GOOGLE_ML = 0.26  # mL / requête médiane Gemini
WATER_MISTRAL_ML = 45   # mL / réponse de 400 tokens

# Palette : fond beige, accent vert
C = dict(bg="#f1e8d6", card="#faf5e9", accent="#3f7d4e", warn="#c26a12",
         danger="#c0392b", text="#2e2820", muted="#6b5f4f", blue="#2f5d9e",
         line="rgba(46,40,32,.16)")


def fr(x, d=2):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


# --------------------------------------------------------------------------- #
# 3. ICÔNES (SVG encodés en base64, pour rester dans un seul fichier)
# --------------------------------------------------------------------------- #
def svg_uri(inner, view="0 0 24 24", stroke=C["accent"], width=1.6):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" fill="none" '
           f'stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" '
           f'stroke-linejoin="round">{inner}</svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


ICON = {
    "user": svg_uri('<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>'),
    "chip": svg_uri('<rect x="6" y="6" width="12" height="12" rx="2"/>'
                    '<path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>'),
    "spark": svg_uri('<path d="M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2z"/>'),
}
LOGO = svg_uri('<circle cx="20" cy="20" r="18"/><circle cx="14" cy="25" r="2"/>'
               '<circle cx="26" cy="14" r="2"/><path d="M15.4 23.6L24.6 15.4"/>',
               view="0 0 40 40", width=1.5)


# --------------------------------------------------------------------------- #
# 4. FIGURES
# --------------------------------------------------------------------------- #
def style(fig, h=340):
    fig.update_layout(
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["text"], family="Outfit, Segoe UI, sans-serif"),
        margin=dict(l=50, r=20, t=60, b=50),
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    return fig


def pct(v):
    return fr(v, 0 if float(v).is_integer() else 1) + " %"


def legend_h():
    return dict(orientation="h", y=-0.2, bgcolor="rgba(0,0,0,0)")


def fig_world_trend():
    colors = {"Monde": C["accent"], "Pays du Nord": C["blue"], "Pays du Sud": C["warn"]}
    fig = go.Figure()
    for name, vals in WORLD.items():
        fig.add_trace(go.Scatter(
            x=WORLD_PERIODS, y=vals, name=name, mode="lines+markers+text",
            line=dict(color=colors[name], width=3), marker=dict(size=8),
            text=[pct(v) for v in vals],
            textposition="bottom center" if name == "Pays du Sud" else "top center"))
    fig.update_yaxes(range=[0, 35], title="% de la population de 15 à 64 ans")
    fig.update_layout(title="Utilisateurs d'IA générative dans le monde [1][2][3]", legend=legend_h())
    return style(fig)


def fig_sources_compare():
    labels = ["Monde<br>(Microsoft, T2 2026)", "France<br>(Microsoft, S2 2025)",
              "France<br>(Arcep-CREDOC, 2025)"]
    vals = [WORLD["Monde"][-1], FR_MICROSOFT, FR_ARCEP]
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=[C["accent"], C["blue"], C["blue"]],
                           text=[pct(v) for v in vals], textposition="outside"))
    fig.update_yaxes(range=[0, 60], title="% de la population")
    fig.update_layout(title="Deux méthodes, un ordre de grandeur proche pour la France [1][5][8]")
    return style(fig)


def fig_firms_trend():
    years = ["2023", "2024", "2025"]
    fig = go.Figure()
    for name, data, col in (("Union européenne [6]", EU_FIRMS, C["blue"]),
                            ("France [7]", FR_FIRMS, C["accent"])):
        vals = [data[int(y)] for y in years]
        fig.add_trace(go.Bar(x=years, y=vals, name=name, marker_color=col,
                             text=[pct(v) for v in vals], textposition="outside"))
    fig.update_yaxes(range=[0, 25], title="% des entreprises")
    fig.update_layout(barmode="group", legend=legend_h(),
                      title="Entreprises de 10 personnes ou plus utilisant l'IA [6][7]")
    return style(fig)


def fig_firms_size():
    labels, vals = list(EU_SIZE), list(EU_SIZE.values())
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=[C["blue"], C["blue"], C["accent"]],
                           text=[pct(v) for v in vals], textposition="outside"))
    fig.update_yaxes(range=[0, 65], title="% des entreprises")
    fig.update_layout(title="Usage de l'IA selon la taille de l'entreprise, UE 2025 [6]")
    return style(fig)


def fig_invest():
    n = len(INVEST_YEARS)
    fig = go.Figure(go.Bar(
        x=[str(y) for y in INVEST_YEARS], y=INVEST_BN,
        marker_color=[C["accent"]] * (n - 1) + [C["warn"]],
        text=[""] * (n - 1) + [f"{fr(INVEST_BN[-1], 1)} Md$"], textposition="outside"))
    fig.update_yaxes(range=[0, 680], title="milliards de dollars")
    fig.update_layout(title="Investissement mondial des entreprises dans l'IA [8]")
    return style(fig)


def fig_dc_demand():
    fig = go.Figure(go.Bar(
        x=["2024", "2030 (projection IEA)"], y=[DC_2024_TWH, DC_2030_TWH],
        marker_color=[C["accent"], C["warn"]],
        text=[f"{DC_2024_TWH} TWh", f"{DC_2030_TWH} TWh"], textposition="outside"))
    fig.update_yaxes(range=[0, 1100], title="TWh par an")
    fig.update_layout(title="Électricité des datacenters dans le monde [9]")
    return style(fig)


# --------------------------------------------------------------------------- #
# 5. COMPOSANTS
# --------------------------------------------------------------------------- #
def eyebrow(num, label):
    return html.Div([html.Span(className="eb-line"), html.Span(num, className="eb-num"),
                     html.Span(label, className="eb-label")], className="eyebrow")


def kpi(value, label, note):
    return html.Div([html.Div(value, className="kpi-v"), html.Div(label, className="kpi-l"),
                     html.Div(note, className="kpi-s")], className="kpi")


def card(title, body, tag=None):
    kids = [html.Span(tag, className="tag")] if tag else []
    kids += [html.H4(title), html.P(body)]
    return html.Div(kids, className="card")


def callout(text, kind="info"):
    return html.Div(text, className=f"callout {kind}")


def sources_block():
    items = [html.Li([f"[{n}] ", html.A(label, href=url, target="_blank", rel="noopener")])
             for n, (label, url) in REFS.items()]
    return html.Div([
        html.H5("Sources"),
        html.Ul(items, style={"listStyle": "none", "paddingLeft": 0}),
        html.P("Valeurs reprises telles quelles des sources, arrondies à l'unité ou à une décimale. "
               "Les mesures d'adoption ne sont pas directement comparables : télémétrie Microsoft [1][2][3], "
               "enquêtes auprès des ménages [4][5], enquêtes auprès des entreprises [6][7], "
               "enquête de cabinet de conseil [8]. Les chiffres de 2030 [9] sont des projections. "
               "Sources consultées et vérifiées le 23 octobre 2026. Détails dans SOURCES.md.")
    ], className="sources")


def pager(i):
    left = dcc.Link("← " + NAV[i - 1][1], href=NAV[i - 1][0], className="btn ghost") if i > 0 else html.Span()
    right = (dcc.Link(NAV[i + 1][1] + " →", href=NAV[i + 1][0], className="btn")
             if i < len(NAV) - 1 else html.Span())
    return html.Div([left, right], className="pager")


def header(idx):
    links = [dcc.Link(label, href=href, className="navlink active" if i == idx else "navlink")
             for i, (href, label) in enumerate(NAV)]
    return html.Header([
        html.Div(id="progress", className="progress",
                 **{"data-idx": str(idx + 1), "data-total": str(len(NAV))}),
        html.Div([
            dcc.Link([html.Img(src=LOGO, className="logo"),
                      html.Div([html.Span("Dans la peau"), html.Span("d'une requête", className="g")],
                               className="brand-t")], href="/", className="brand"),
            html.Nav(links, className="nav"),
            html.Div(["PAGE ", html.Span(f"{idx + 1} / {len(NAV)}", className="g")], className="pagenum"),
        ], className="hd-in"),
    ], className="hd")


# --------------------------------------------------------------------------- #
# 6. PAGES
# --------------------------------------------------------------------------- #
def hero():
    steps = [("user", "Votre question", "Une consigne est envoyée", False),
             ("chip", "Le modèle traite", "Des calculs sont effectués", True),
             ("spark", "Une réponse", "Le résultat est renvoyé", False)]
    flow = []
    for i, (ic, title, desc, on) in enumerate(steps):
        if i:
            flow.append(html.Div("→", className="farrow"))
        flow.append(html.Div([html.Div(html.Img(src=ICON[ic]), className="ficon"),
                              html.H4(title), html.P(desc)],
                             className="fstep on" if on else "fstep"))
    return html.Section(html.Div([
        html.Div([
            eyebrow("01", "COMPRENDRE L'IA"),
            html.H1(["Une requête.", html.Span("Des machines.", className="g")], className="h-big"),
            html.P("En moins de quatre ans, l'IA générative est passée de la curiosité à l'usage courant. "
                   "Mesurons son essor avec des sources officielles, puis suivons le parcours d'une question "
                   "et les ressources matérielles qui se cachent derrière la réponse.", className="lead"),
            html.Div([dcc.Link(["Suivre une requête ", html.Span("→")], href="/requete", className="btn"),
                      dcc.Link("Tester le calculateur", href="/calculateur", className="btn ghost")],
                     className="btns"),
        ]),
        html.Div(flow, className="flow"),
    ], className="wrap hero"), className="hero-bg")


def page_1():
    body = html.Div([
        html.Div([
            html.H2("Qu'est-ce que l'IA générative ?"),
            html.P("Une intelligence artificielle est un programme qui apprend à partir de données "
                   "pour accomplir des tâches qui demandent habituellement de l'intelligence humaine : "
                   "reconnaître, prédire, traduire, rédiger. L'IA générative produit du contenu nouveau "
                   "(texte, image, code) à partir d'une consigne.", className="lead"),
            html.Div([
                card("1. Des données", "Le modèle est nourri de très grandes quantités de textes, d'images ou de code.", "Collecte"),
                card("2. L'entraînement", "Des milliers de puces ajustent des milliards de paramètres pendant des semaines. "
                     "Cette étape est faite une fois par modèle.", "Apprentissage"),
                card("3. L'inférence", "Chaque fois que vous posez une question, le modèle calcule une réponse "
                     "dans un datacenter. Cette étape est répétée à chaque usage.", "Usage"),
            ], className="grid3"),
            callout("Chaque étape repose sur du matériel physique : puces, serveurs, bâtiments, électricité, "
                    "eau de refroidissement. C'est là que se situe l'impact environnemental.", "info"),
        ], className="sec"),

        html.Div([
            html.H2("Combien de personnes utilisent l'IA générative ?"),
            html.P("Il n'existe pas de mesure unique : chaque organisme observe un périmètre différent. "
                   "Voici les plus solides, du monde jusqu'à la France.", className="lead"),
            html.Div([
                kpi("18,8 %", "Population mondiale de 15 à 64 ans utilisant l'IA générative, juin 2026",
                    "Près d'une personne sur cinq ; 16,3 % fin 2025 [1][2]"),
                kpi("28,8 % vs 16,2 %", "Pays du Nord vs pays du Sud, 2e trimestre 2026",
                    "Un écart de 12,6 points, qui continue de se creuser [1]"),
                kpi("> 1/3", "Individus des pays de l'OCDE utilisant l'IA générative en 2025",
                    "Environ 3 étudiants de 16 ans et plus sur 4 [4]"),
                kpi("48 %", "Population française de 12 ans et plus, enquête de juin 2025",
                    "+15 points en un an [5]"),
            ], className="kpis"),
            html.Div([
                html.Div(dcc.Graph(figure=fig_world_trend(), config={"displayModeBar": False}), className="col"),
                html.Div(dcc.Graph(figure=fig_sources_compare(), config={"displayModeBar": False}), className="col"),
            ], className="row"),
            callout("Attention aux chiffres « mondiaux ». Le « 53 % d'adoption en trois ans » souvent cité depuis "
                    "le rapport Stanford AI Index 2026 provient d'enquêtes auprès des 18-64 ans aux États-Unis, "
                    "comparées aux enquêtes américaines sur l'ordinateur et Internet [8] : ce n'est pas une mesure "
                    "de la population mondiale. La mesure mondiale de référence est celle de Microsoft (18,8 %), "
                    "construite à partir de données d'usage anonymisées et redressées selon le parc d'appareils, "
                    "l'accès à Internet et la population. Microsoft prévoit d'élargir sa mesure aux nouveaux outils, "
                    "ce qui devrait faire monter ce chiffre, surtout en Chine [1].", "warn"),
        ], className="sec"),

        html.Div([
            html.H2("Et du côté des entreprises ?"),
            html.P("Les statistiques officielles interrogent un échantillon représentatif d'entreprises. "
                   "Elles portent sur l'ensemble des technologies d'IA (analyse de texte, génération de contenu, "
                   "analyse de données…), pas uniquement sur l'IA générative.", className="lead"),
            html.Div([
                kpi("20 %", "Entreprises de l'UE (10 personnes ou plus) utilisant au moins une technologie d'IA, 2025",
                    "13,5 % en 2024 et 8,1 % en 2023 [6]"),
                kpi("18 %", "Entreprises françaises (10 salariés ou plus), 2025",
                    "6 % en 2023, 10 % en 2024 : usage triplé en deux ans [7]"),
                kpi("55 % vs 17 %", "Grandes entreprises vs petites entreprises (UE, 2025)",
                    "250 salariés ou plus vs 10 à 49 ; 30 % pour les moyennes [6]"),
                kpi("62,5 %", "Secteur de l'information et de la communication (UE, 2025)",
                    "Contre 10,8 % dans la construction [6]"),
            ], className="kpis"),
            html.Div([
                html.Div(dcc.Graph(figure=fig_firms_trend(), config={"displayModeBar": False}), className="col"),
                html.Div(dcc.Graph(figure=fig_firms_size(), config={"displayModeBar": False}), className="col"),
            ], className="row"),
            callout("Pourquoi 20 % ici et 88 % ailleurs ? Le rapport Stanford cite 88 % d'organisations utilisant "
                    "l'IA dans au moins une fonction en 2025 [8] : c'est une enquête auto-déclarée, que Stanford "
                    "lui-même invite à lire comme indicative. Eurostat interroge 157 000 des 1,53 million "
                    "d'entreprises de l'UE, dont 83 % de petites [6]. Deux périmètres, deux résultats : "
                    "il faut toujours lire la définition avant de comparer.", "warn"),
            callout("Le principal frein : parmi les entreprises qui avaient envisagé l'IA sans l'utiliser, "
                    "71 % citent le manque de compétences, 53 % l'incertitude juridique et 49 % la protection "
                    "des données [6].", "info"),
        ], className="sec"),

        html.Div([
            html.H2("Un écosystème : des assistants et des modèles"),
            html.P("Derrière l'expression « IA générative » se cachent plusieurs entreprises, plusieurs produits "
                   "et, pour chacun, plusieurs modèles. Les pages suivantes comparent ces modèles ; "
                   "voici d'abord les deux grandes familles.", className="lead"),
            html.Div([
                card("Des assistants prêts à l'emploi",
                     "ChatGPT (OpenAI), Gemini (Google) et Claude (Anthropic) sont proposés comme services en ligne : "
                     "démarrage très simple, hébergement et maintenance assurés par le fournisseur, "
                     "et accès possible par API pour créer ses propres outils.", "ChatGPT · Gemini · Claude"),
                card("Des modèles à récupérer",
                     "Llama (Meta) et Gemma (Google) sont conçus pour être téléchargés et intégrés à ses propres "
                     "outils, parfois exécutés en local. Plus de contrôle sur les données et la personnalisation, "
                     "mais installation et maintenance à votre charge.", "Llama · Gemma"),
                card("Plusieurs modèles par famille",
                     "Chaque famille compte plusieurs versions et tailles de modèles. Leur performance et leur "
                     "consommation de ressources dépendent de la version, de la taille, du matériel et de la tâche : "
                     "c'est ce que les pages suivantes analysent.", "Pages suivantes"),
            ], className="grid3"),
            callout("Un modèle local n'est pas forcément moins performant ni automatiquement plus sécurisé : "
                    "tout dépend de la version, de la taille du modèle, du matériel et de la configuration. "
                    "Un assistant en ligne peut, de son côté, combiner son modèle avec des outils externes.", "info"),
        ], className="sec"),

        html.Div([
            html.H2("Un essor rapide, des ressources bien réelles"),
            callout("Problématique — Face à l'opacité du secteur de l'IA générative sur son impact "
                    "environnemental, comment mobiliser les données existantes pour éclairer le débat "
                    "public et permettre des choix avisés ?", "question"),
            html.Div([
                kpi(f"{fr(INVEST_BN[-1], 1)} Md$", "Investissement mondial des entreprises dans l'IA, 2025",
                    "+129,9 % en un an ; 170,9 Md$ de financements privés visent l'IA générative [8]"),
                kpi(f"{DC_2024_TWH} → {DC_2030_TWH} TWh", "Électricité des datacenters, 2024 → 2030 (projection)",
                    "≈ 1,5 % de l'électricité mondiale en 2024 ; plus que le Japon aujourd'hui en 2030 [9]"),
                kpi("×4", "Demande des datacenters optimisés pour l'IA d'ici 2030",
                    "Projection : l'IA est le principal moteur de la hausse [9]"),
            ], className="kpis"),
            html.Div([
                html.Div(dcc.Graph(figure=fig_invest(), config={"displayModeBar": False}), className="col"),
                html.Div(dcc.Graph(figure=fig_dc_demand(), config={"displayModeBar": False}), className="col"),
            ], className="row"),
            callout("L'adoption se mesure avec des statistiques publiques ; l'électricité de 2030 reste une "
                    "projection ; et l'impact environnemental d'une requête n'est connu que par des déclarations "
                    "d'entreprises dont les méthodes ne sont pas comparables. C'est tout l'enjeu des pages suivantes.",
                    "warn"),
        ], className="sec"),

        html.Div([
            html.H2("Quatre objectifs pour ce parcours"),
            html.Div([
                card("Comprendre", "Savoir ce qu'est l'IA générative et d'où viennent ses besoins en ressources.", "1"),
                card("Mesurer", "Rassembler les chiffres publiés : entraînement, requêtes, datacenters, eau.", "2"),
                card("Comparer", "Confronter les sources et repérer ce qui n'est pas comparable.", "3"),
                card("Agir", "Identifier des alternatives et les données à exiger pour décider.", "4"),
            ], className="grid4"),
        ], className="sec"),

        sources_block(),
        pager(0),
    ], className="wrap")
    return html.Div([hero(), body], className="page")


def placeholder(i):
    name = NAV[i][1]
    return html.Div(html.Section(html.Div([
        eyebrow(f"0{i + 1}", name.upper()),
        html.H1(name, className="h-big"),
        html.P("Cette page sera construite à l'étape suivante.", className="lead"),
        pager(i),
    ], className="wrap ph"), className="hero-bg"), className="page")


# --------------------------------------------------------------------------- #
# 7. APPLICATION
# --------------------------------------------------------------------------- #
app = Dash(
    __name__, title="Dans la peau d'une requête",
    external_stylesheets=["https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700"
                          "&family=JetBrains+Mono:wght@500&display=swap"],
)
server = app.server

ROOT = (":root{" + ";".join(f"--{k}:{v}" for k, v in C.items()) + "}")

CSS = """
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-family:'Outfit','Segoe UI',system-ui,sans-serif;line-height:1.55}
a{color:var(--accent)}
.g{color:var(--accent);font-weight:600}

/* En-tête */
.hd{position:sticky;top:0;z-index:50;background:rgba(241,232,214,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.hd-in{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:0 40px;height:96px}
.brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:var(--text);font-size:14px;font-weight:500;line-height:1.2}
.brand-t{display:flex;flex-direction:column}
.logo{width:38px;height:38px}
.nav{display:flex;gap:4px;align-self:stretch}
.navlink{position:relative;display:flex;align-items:center;padding:0 16px;color:var(--muted);text-decoration:none;font-size:15px;white-space:nowrap;transition:color .2s,background .2s}
.navlink:hover{color:var(--text);background:rgba(63,125,78,.12)}
.navlink::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:3px;background:var(--accent);transform:scaleX(0);transform-origin:left;transition:transform .25s}
.navlink:hover::after{transform:scaleX(.5)}
.navlink.active{color:var(--text);font-weight:600}
.navlink.active::after{transform:scaleX(1)}
.pagenum{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.1em;color:var(--muted);white-space:nowrap}
.progress{position:absolute;left:0;top:0;height:4px;width:2%;background:var(--accent);transition:width .15s linear;z-index:2}

/* Mise en page */
.wrap{max-width:1280px;margin:0 auto;padding:0 40px}
.page{animation:fade .5s ease}
@keyframes fade{from{opacity:0}to{opacity:1}}
.hero-bg{background-image:linear-gradient(rgba(46,40,32,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(46,40,32,.05) 1px,transparent 1px);background-size:64px 64px}
.hero{min-height:calc(100vh - 100px);display:grid;grid-template-columns:1.05fr 1fr;gap:56px;align-items:center;padding-top:56px;padding-bottom:56px}
.ph{padding-top:96px;padding-bottom:96px;min-height:calc(100vh - 100px)}
.eyebrow{display:flex;align-items:center;gap:14px;margin-bottom:28px}
.eb-line{width:48px;height:1px;background:var(--accent)}
.eb-num{width:32px;height:32px;border:1px solid var(--accent);border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--accent)}
.eb-label{font-family:'JetBrains Mono',monospace;font-size:13px;letter-spacing:.12em;color:var(--accent)}
.h-big{font-size:clamp(46px,7vw,98px);line-height:1;letter-spacing:-.035em;font-weight:600;margin:0 0 28px}
.h-big .g{display:block}
.lead{font-size:19px;color:var(--muted);max-width:640px}
.btns{display:flex;gap:14px;flex-wrap:wrap;margin-top:32px}
.btn{display:inline-flex;align-items:center;gap:10px;padding:15px 26px;background:var(--accent);color:#fff;text-decoration:none;font-weight:600;border:1px solid var(--accent);transition:transform .2s,box-shadow .2s,background .2s,color .2s}
.btn:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(63,125,78,.3)}
.btn.ghost{background:transparent;color:var(--text);border-color:var(--text)}
.btn.ghost:hover{background:var(--text);color:var(--bg);box-shadow:none}

/* Schéma du hero */
.flow{display:flex;align-items:center;padding:36px;border:1px solid var(--line);background:rgba(255,255,255,.35)}
.fstep{flex:1;text-align:center;padding:34px 14px 30px;background:var(--card);border-top:2px solid var(--line);transition:transform .25s,border-color .25s,box-shadow .25s}
.fstep.on,.fstep:hover{border-top-color:var(--accent)}
.fstep:hover{transform:translateY(-4px);box-shadow:0 10px 24px rgba(46,40,32,.12)}
.ficon{width:64px;height:64px;border-radius:50%;border:1px solid var(--line);display:flex;align-items:center;justify-content:center;margin:0 auto 22px}
.ficon img{width:28px;height:28px}
.fstep h4{margin:0 0 10px;font-size:17px;line-height:1.25}
.fstep p{margin:0;font-size:13px;color:var(--muted)}
.farrow{flex:0 0 36px;text-align:center;color:var(--muted);font-size:20px}

/* Sections */
.sec{padding:72px 0 0}
.sec h2{font-size:clamp(28px,3.6vw,44px);line-height:1.1;letter-spacing:-.02em;margin:0 0 18px;font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:18px 0}
.kpi,.card{background:var(--card);border-radius:14px;padding:18px;border:1px solid rgba(0,0,0,.08);box-shadow:0 1px 3px rgba(0,0,0,.05);transition:transform .2s,border-color .2s,box-shadow .2s}
.kpi:hover,.card:hover{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 10px 24px rgba(46,40,32,.10)}
.kpi-v{font-size:28px;font-weight:700;color:var(--accent)}
.kpi-l{font-size:14px;margin-top:4px}
.kpi-s{font-size:12px;color:var(--muted);margin-top:8px}
.row{display:flex;gap:16px;flex-wrap:wrap}
.col{flex:1 1 420px;min-width:300px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin-top:24px}
.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.card h4{margin:8px 0 6px}
.card p{margin:0;color:var(--muted);font-size:15px}
.tag{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#fff;background:var(--accent);padding:3px 9px;border-radius:999px;font-weight:600}
.callout{border-left:4px solid var(--accent);background:rgba(63,125,78,.10);padding:14px 18px;border-radius:8px;margin:18px 0}
.callout.warn{border-color:var(--warn);background:rgba(194,106,18,.10)}
.callout.question{border-color:var(--blue);background:rgba(47,93,158,.08);font-size:17px}
.sources{margin-top:72px;padding-top:12px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
.sources h5{margin:0 0 6px}
.pager{display:flex;justify-content:space-between;margin:48px 0 72px}

@media (max-width:900px){
  .hero{grid-template-columns:1fr}
  .hd-in{padding:0 16px;height:72px}
  .pagenum,.brand-t{display:none}
  .nav{overflow-x:auto;overflow-y:hidden;scrollbar-width:none}
  .nav::-webkit-scrollbar{display:none}
  .navlink::after{bottom:0}
  .wrap{padding:0 20px}
  .flow{padding:14px}
}
"""

JS = """
(function(){
  function update(){
    var bar = document.getElementById('progress'); if(!bar) return;
    var idx = parseInt(bar.dataset.idx || '1', 10), total = parseInt(bar.dataset.total || '6', 10);
    var h = document.documentElement.scrollHeight - window.innerHeight;
    var frac = h > 0 ? Math.min(1, Math.max(0, window.scrollY / h)) : 0;
    bar.style.width = Math.max(((idx - 1) + frac) / total * 100, 2) + '%';
  }
  window.addEventListener('scroll', update, {passive:true});
  window.addEventListener('resize', update);
  new MutationObserver(update).observe(document.body, {childList:true, subtree:true});
  window.__updateProgress = update;
})();
"""

app.index_string = (
    "<!DOCTYPE html>\n<html lang=\"fr\"><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}"
    "<style>" + ROOT + CSS + "</style></head>\n"
    "<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer>"
    "<script>" + JS + "</script></body></html>"
)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="header"),
    html.Div(id="page"),
    html.Div(id="scroll-dummy", style={"display": "none"}),
])

# Retour en haut de page à chaque changement d'onglet, puis mise à jour de la barre
app.clientside_callback(
    "function(p){window.scrollTo(0,0);"
    "setTimeout(function(){if(window.__updateProgress){window.__updateProgress();}},60);return '';}",
    Output("scroll-dummy", "children"), Input("url", "pathname"),
)


@callback(Output("header", "children"), Output("page", "children"), Input("url", "pathname"))
def route(pathname):
    hrefs = [h for h, _ in NAV]
    idx = hrefs.index(pathname) if pathname in hrefs else 0
    return header(idx), (page_1() if idx == 0 else placeholder(idx))


if __name__ == "__main__":
    URL = "http://127.0.0.1:8050"
    # En mode debug, Flask relance le script une 2e fois : on n'ouvre le navigateur qu'une fois.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.5, lambda: webbrowser.open(URL)).start()
    app.run(debug=True, port=8050)