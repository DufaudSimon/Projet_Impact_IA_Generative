"""
IA générative & environnement — Page 1 : comprendre et poser le problème.

Problématique : face à l'opacité du secteur de l'IA générative sur son impact
environnemental, comment mobiliser les données existantes pour éclairer le débat
public et permettre des choix avisés ?

Lancer :  pip install -r requirements.txt  &&  python app.py
Puis ouvrir http://127.0.0.1:8050

Toutes les valeurs chiffrées sont référencées [1], [2]… et listées dans SOURCES.md.
"""

from dash import Dash, html, dcc
import plotly.graph_objects as go

# --------------------------------------------------------------------------- #
# 1. SOURCES (numérotation utilisée dans l'interface et dans SOURCES.md)
# --------------------------------------------------------------------------- #
REFS = {
    1: ("IEA, « Energy and AI » (communiqué, 10 avril 2025)",
        "https://www.iea.org/news/ai-is-set-to-drive-surging-electricity-demand-from-data-centres-while-offering-the-potential-to-transform-how-the-energy-sector-works"),
    2: ("Scientific American, « Data Centers Will Use Twice as Much Energy by 2030 » (analyse du rapport IEA)",
        "https://scientificamerican.com/article/ai-will-drive-doubling-of-data-center-energy-demand-by-2030"),
    3: ("Data Center Dynamics, « Google: median Gemini prompt uses 0.24 watt-hours… » (méthodologie Google, 2025)",
        "https://www.datacenterdynamics.com/en/news/google-median-gemini-prompt-uses-024-watt-hours-of-power-and-consumes-026ml-of-water/"),
    4: ("Mistral AI, « Our contribution to a global environmental standard for AI » (analyse de cycle de vie, 2025)",
        "https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai"),
}

# Valeurs affichées -> toutes issues des sources ci-dessus
DC_2024_TWH = 415      # [1][2]
DC_2030_TWH = 945      # [1][2]
AI_SHARE_2024 = 15     # % de l'énergie totale des datacenters, serveurs IA [2]
CO2_GOOGLE_G = 0.03    # g CO2e / requête médiane Gemini [3]
CO2_MISTRAL_G = 1.14   # g CO2e / réponse de 400 tokens [4]
WATER_GOOGLE_ML = 0.26  # mL / requête médiane Gemini [3]
WATER_MISTRAL_ML = 45   # mL / réponse de 400 tokens [4]

C = dict(bg="#f1e8d6", card="#faf5e9", accent="#3f7d4e", warn="#c26a12",
         danger="#c0392b", text="#2e2820", muted="#6b5f4f", blue="#2f5d9e")


def fr(x, d=2):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def style(fig, h=340):
    fig.update_layout(
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["text"], family="Inter, Segoe UI, sans-serif"),
        margin=dict(l=50, r=20, t=60, b=50),
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    return fig


# --------------------------------------------------------------------------- #
# 2. FIGURES
# --------------------------------------------------------------------------- #
def fig_dc_demand():
    fig = go.Figure(go.Bar(
        x=["2024", "2030 (projection IEA)"], y=[DC_2024_TWH, DC_2030_TWH],
        marker_color=[C["accent"], C["warn"]],
        text=[f"{DC_2024_TWH} TWh", f"{DC_2030_TWH} TWh"], textposition="outside"))
    fig.update_yaxes(range=[0, 1100], title="TWh par an")
    fig.update_layout(title="Électricité des datacenters dans le monde [1][2]")
    return style(fig)


def fig_ai_share():
    fig = go.Figure(go.Pie(
        labels=["Serveurs IA", "Autres usages (serveurs classiques, stockage, réseau, refroidissement…)"],
        values=[AI_SHARE_2024, 100 - AI_SHARE_2024], hole=0.62,
        marker_colors=[C["danger"], "#ddd0b4"], textinfo="percent", sort=False))
    fig.update_layout(title="Part des serveurs IA dans l'énergie des datacenters, 2024 [2]",
                      legend=dict(orientation="h", y=-0.15, bgcolor="rgba(0,0,0,0)"))
    return style(fig)


# --------------------------------------------------------------------------- #
# 3. COMPOSANTS
# --------------------------------------------------------------------------- #
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
        html.P("[1][2] : valeurs reprises telles quelles. "
               "Écarts « ×38 » et « ×170 » : calculs maison à partir de [3] et [4] "
               "(1,14 ÷ 0,03 ≈ 38 ; 45 ÷ 0,26 ≈ 173), entre deux méthodologies "
               "différentes, donc indicatifs. Détails dans SOURCES.md.")
    ], className="sources")


# --------------------------------------------------------------------------- #
# 4. PAGE 1
# --------------------------------------------------------------------------- #
def layout():
    ratio_co2 = CO2_MISTRAL_G / CO2_GOOGLE_G
    ratio_water = WATER_MISTRAL_ML / WATER_GOOGLE_ML
    return html.Div([
        html.Div([
            html.Div("1 / 5 · COMPRENDRE", className="eyebrow"),
            html.H1("L'IA générative a un coût physique. Combien, au juste ?"),
            html.P("Une intelligence artificielle est un programme qui apprend à partir de données "
                   "pour accomplir des tâches qui demandent habituellement de l'intelligence humaine : "
                   "reconnaître, prédire, traduire, rédiger. L'IA générative produit du contenu nouveau "
                   "(texte, image, code) à partir d'une consigne.", className="lead"),
        ], className="hero"),

        html.H3("Comment ça marche, en trois temps"),
        html.Div([
            card("1. Des données", "Le modèle est nourri de très grandes quantités de textes, d'images ou de code.", "Collecte"),
            card("2. L'entraînement", "Des milliers de puces ajustent des milliards de paramètres pendant des semaines. "
                 "Cette étape est faite une fois par modèle.", "Apprentissage"),
            card("3. L'inférence", "Chaque fois que vous posez une question, le modèle calcule une réponse "
                 "dans un datacenter. Cette étape est répétée à chaque usage.", "Usage"),
        ], className="grid3"),
        callout("Chaque étape repose sur du matériel physique : puces, serveurs, bâtiments, électricité, "
                "eau de refroidissement. C'est là que se situe l'impact environnemental.", "info"),

        html.H3("Le problème : un impact réel, mais mal documenté"),
        callout("Problématique — Face à l'opacité du secteur de l'IA générative sur son impact "
                "environnemental, comment mobiliser les données existantes pour éclairer le débat "
                "public et permettre des choix avisés ?", "question"),

        html.H3("Quatre chiffres pour poser le décor"),
        html.Div([
            kpi(f"{DC_2024_TWH} → {DC_2030_TWH} TWh", "Électricité des datacenters, 2024 → 2030",
                "Plus que doubler ; équivalent de la consommation actuelle du Japon [1]"),
            kpi("×4", "Demande des datacenters optimisés pour l'IA d'ici 2030",
                "Projection : l'IA est le principal moteur de la hausse [1]"),
            kpi(f"×{fr(ratio_co2, 0)}", "Écart sur le CO₂ par requête entre deux déclarations",
                f"{fr(CO2_GOOGLE_G)} g (Google) vs {fr(CO2_MISTRAL_G)} g (Mistral) [3][4]"),
            kpi(f"×{fr(ratio_water, 0)}", "Écart sur l'eau par requête entre deux déclarations",
                f"{fr(WATER_GOOGLE_ML)} mL (Google) vs {WATER_MISTRAL_ML} mL (Mistral) [3][4]"),
        ], className="kpis"),

        html.Div([
            html.Div(dcc.Graph(figure=fig_dc_demand(), config={"displayModeBar": False}), className="col"),
            html.Div(dcc.Graph(figure=fig_ai_share(), config={"displayModeBar": False}), className="col"),
        ], className="row"),

        callout("Les deux derniers chiffres ne comparent pas la même chose : Google mesure la chaîne de service "
                "(hors entraînement, réseau, terminaux et stockage) et l'eau de refroidissement direct [3], "
                "Mistral inclut le cycle de vie, y compris la fabrication du matériel [4]. "
                "C'est précisément ce manque de standard qui rend le débat difficile.", "warn"),

        html.H3("Quatre objectifs pour ce parcours"),
        html.Div([
            card("Comprendre", "Savoir ce qu'est l'IA générative et d'où viennent ses besoins en ressources.", "1"),
            card("Mesurer", "Rassembler les chiffres publiés : entraînement, requêtes, datacenters, eau.", "2"),
            card("Comparer", "Confronter les sources et repérer ce qui n'est pas comparable.", "3"),
            card("Agir", "Identifier des alternatives et les données à exiger pour décider.", "4"),
        ], className="grid4"),

        sources_block(),
    ], className="container")


# --------------------------------------------------------------------------- #
# 5. APPLICATION
# --------------------------------------------------------------------------- #
app = Dash(__name__, title="IA & environnement")
server = app.server

CSS = f"""
*{{box-sizing:border-box}}
body{{margin:0;background:{C['bg']};color:{C['text']};font-family:Inter,'Segoe UI',system-ui,sans-serif;line-height:1.55}}
a{{color:{C['accent']}}}
.container{{max-width:1100px;margin:0 auto;padding:32px 24px 64px}}
.hero{{padding:24px 0 8px}}
.eyebrow{{letter-spacing:.14em;font-size:12px;color:{C['accent']};font-weight:600}}
h1{{font-size:clamp(28px,4.4vw,46px);line-height:1.12;margin:8px 0 14px}}
h3{{margin:40px 0 14px;font-size:22px}}
.lead{{font-size:18px;color:{C['muted']};max-width:780px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:18px 0}}
.kpi{{background:{C['card']};border-radius:14px;padding:18px;border:1px solid rgba(0,0,0,.08);box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.kpi-v{{font-size:28px;font-weight:700;color:{C['accent']}}}
.kpi-l{{font-size:14px;margin-top:4px}}
.kpi-s{{font-size:12px;color:{C['muted']};margin-top:8px}}
.row{{display:flex;gap:16px;flex-wrap:wrap}}
.col{{flex:1 1 420px;min-width:300px}}
.grid3{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}
.grid4{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}
.card{{background:{C['card']};border-radius:14px;padding:18px;border:1px solid rgba(0,0,0,.08);box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.card h4{{margin:8px 0 6px}} .card p{{margin:0;color:{C['muted']};font-size:15px}}
.tag{{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#ffffff;background:{C['accent']};
  padding:3px 9px;border-radius:999px;font-weight:600}}
.callout{{border-left:4px solid {C['accent']};background:rgba(63,125,78,.10);padding:14px 18px;border-radius:8px;margin:18px 0}}
.callout.warn{{border-color:{C['warn']};background:rgba(217,119,6,.10)}}
.callout.question{{border-color:{C['blue']};background:rgba(37,99,235,.08);font-size:17px}}
.sources{{margin-top:36px;padding-top:12px;border-top:1px solid rgba(0,0,0,.12);font-size:13px;color:{C['muted']}}}
.sources h5{{margin:0 0 6px}}
"""

app.index_string = f"""<!DOCTYPE html>
<html lang="fr"><head>{{%metas%}}<title>{{%title%}}</title>{{%favicon%}}{{%css%}}
<style>{CSS}</style></head>
<body>{{%app_entry%}}<footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer></body></html>"""

app.layout = layout

if __name__ == "__main__":
    import os
    import threading
    import webbrowser

    URL = "http://127.0.0.1:8050"
    # En mode debug, Flask relance le script une 2e fois : on n'ouvre le navigateur qu'une fois.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.5, lambda: webbrowser.open(URL)).start()
    app.run(debug=False, port=8050)