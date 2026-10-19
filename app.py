"""
DANS LA PEAU D'UNE REQUÊTE : sensibilisation à l'impact des IA génératives.

Installation :  python -m pip install dash plotly
Lancement    :  python app.py   puis ouvrir http://127.0.0.1:8050

RÈGLE DU PROJET : chaque chiffre porte un statut.
  Mesuré  = publié par une mesure ou calculable exactement (ex. taille d'un texte)
  Estimé  = ordre de grandeur, déclaration d'opérateur ou hypothèse pédagogique
  Inconnu = donnée non publiée : on ne l'invente pas

DONNÉES RÉELLES : déposez un fichier  data/ai_energy_score.csv  (colonnes :
modele,tache,wh_pour_1000,source,statut) issu d'AI Energy Score / Compar:IA et la
page « Comparer » l'affichera automatiquement.
"""
import csv
import math
import os

import plotly.graph_objects as go
from dash import Dash, ctx, dcc, html, Input, Output, State

# --------------------------------------------------------------------------- #
# Données
# --------------------------------------------------------------------------- #
GREEN, TEAL, AMBER, BLUE = "#5BE3A1", "#26C6DA", "#F2B53C", "#6C86B8"
STATUS_COLOR = {"mesure": GREEN, "estime": AMBER, "inconnu": BLUE}
STATUS_LABEL = {"mesure": "Mesuré", "estime": "Estimé", "inconnu": "Inconnu"}

# Classes de modèles. Les Wh par 1000 tokens sont des HYPOTHÈSES PÉDAGOGIQUES
# (proportionnelles à la taille), pas des mesures. "mult" = tokens cachés de raisonnement.
MODELS = {
    "petit": {"label": "Petit modèle ouvert (≈ 8 Md de paramètres, ex. Llama 3.1 8B)",
              "short": "Petit (8 Md)", "params": 8e9, "wh1k": 0.05, "mult": 1},
    "moyen": {"label": "Modèle moyen (≈ 70 Md de paramètres, ex. Llama 3.1 70B)",
              "short": "Moyen (70 Md)", "params": 70e9, "wh1k": 0.2, "mult": 1},
    "grand": {"label": "Très grand modèle (≈ 405 Md de paramètres, ex. Llama 3.1 405B)",
              "short": "Très grand (405 Md)", "params": 405e9, "wh1k": 1.0, "mult": 1},
    "raison": {"label": "Modèle de raisonnement (taille non publiée, calcul indicatif à 70 Md)",
               "short": "Raisonnement", "params": 70e9, "wh1k": 0.2, "mult": 10},
}
CO2_G_PER_KWH = {"France": 50, "Monde": 450}  # ordres de grandeur, à actualiser (RTE éCO2mix)

# Valeurs publiées (ordres de grandeur). Wh par requête ou par génération.
REFERENCES = [
    ("Texte (moyenne de petits modèles testés)", 0.047, "mesure", "Luccioni et al., 2023-24"),
    ("Requête texte Gemini (médiane)", 0.24, "estime", "Google, 2025 (déclaré par l'opérateur)"),
    ("Requête typique GPT-4o", 0.3, "estime", "Epoch AI, 2025 (estimation externe)"),
    ("Image générée (modèle le plus coûteux testé)", 2.9, "mesure", "Luccioni et al., 2023-24"),
    ("Vidéo de 5 s (modèle ouvert)", 944, "mesure", "MIT Technology Review, 2025"),
]

STAGES = [("💬", "Votre question"), ("📡", "Le réseau"), ("🏢", "Le centre de données"),
          ("🧠", "Le calcul du modèle"), ("🖥️", "La réponse")]

SOURCES = [
    ("AI Energy Score", "https://huggingface.co/AIEnergyScore"),
    ("Compar:IA", "https://comparia.beta.gouv.fr"),
    ("IEA", "https://www.iea.org/reports/energy-and-ai"),
    ("Eurostat", "https://ec.europa.eu/eurostat"),
    ("RTE éCO2mix", "https://www.rte-france.com/eco2mix"),
    ("ADEME", "https://www.ademe.fr"),
]

# --------------------------------------------------------------------------- #
# Style
# --------------------------------------------------------------------------- #
CSS = """
:root{--bg:#08162B;--panel:#0E2340;--panel2:#132C50;--green:#5BE3A1;--teal:#26C6DA;--amber:#F2B53C;
--blue:#6C86B8;--text:#E8F0FA;--mute:#9DB0CC;--line:#27406A}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:"Segoe UI",system-ui,Helvetica,Arial,sans-serif;line-height:1.6}
h1,h2,h3{margin:0 0 .5em;line-height:1.2} h1{font-size:2.5rem} h2{font-size:1.5rem} h3{font-size:1.1rem}
a{color:var(--teal)}
.shell{display:flex;min-height:100vh}
.side{width:250px;flex:none;background:#061021;border-right:1px solid var(--line);padding:26px 16px;position:sticky;top:0;height:100vh}
.brand{font-weight:700;font-size:1.15rem;text-align:center;margin-bottom:4px}
.tag{font-size:.8rem;color:var(--teal);text-align:center;margin-bottom:26px}
.side a.nav{display:block;color:var(--mute);text-decoration:none;padding:10px 14px;border-radius:10px;margin-bottom:6px}
.side a.nav:hover,.side a.nav:focus-visible{color:#fff;background:var(--panel);outline:none}
.side a.nav.on{color:#fff;background:#14403F;box-shadow:inset 3px 0 0 var(--green)}
.tipbox{margin-top:26px;border:1px solid var(--line);border-radius:12px;padding:14px;font-size:.88rem;color:var(--mute)}
.content{flex:1;min-width:0;padding:34px 44px 18px}
.hero h1 span{color:var(--green)}
.sub{font-size:1.15rem;color:var(--mute);max-width:60ch}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px 24px;margin:16px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.btn{display:inline-block;background:var(--green);color:#06281A;font-weight:700;border:0;border-radius:10px;
 padding:11px 20px;cursor:pointer;text-decoration:none;margin:6px 8px 6px 0;font-size:1rem}
.btn.ghost{background:transparent;color:var(--text);border:1px solid var(--line)}
.btn:hover,.btn:focus-visible{filter:brightness(1.12);outline:2px solid var(--teal)}
.badge{display:inline-block;border-radius:99px;padding:1px 10px;font-size:.78rem;font-weight:600;margin-left:8px}
.badge.mesure{background:rgba(91,227,161,.18);color:var(--green)}
.badge.estime{background:rgba(242,181,60,.18);color:var(--amber)}
.badge.inconnu{background:rgba(108,134,184,.25);color:#B5C6E6}
.srow{display:flex;justify-content:space-between;gap:12px;padding:10px 0;border-bottom:1px solid var(--line)}
.srow:last-child{border:0}.srow small{color:var(--mute);display:block}
.tline{display:flex;margin:22px 0 8px}
.node{flex:1;text-align:center;position:relative;min-width:0;padding:0 4px}
.node .ico{font-size:1.8rem}
.node .lab{display:inline-block;border:1px solid var(--line);border-radius:99px;padding:2px 10px;font-size:.82rem;margin:4px 0 10px}
.dotrow{position:relative;height:28px}
.node:not(:first-child) .dotrow::before{content:"";position:absolute;top:13px;left:-50%;width:100%;border-top:2px dashed var(--line)}
.node.done:not(:first-child) .dotrow::before,.node.now:not(:first-child) .dotrow::before{border-top:2px dashed var(--green)}
.dot{width:28px;height:28px;border-radius:50%;border:2px solid var(--blue);background:var(--bg);margin:0 auto;position:relative;z-index:1;font-size:.8rem;line-height:24px}
.node.done .dot{border-color:var(--green);color:var(--green)}
.node.now .dot{border-color:var(--green);box-shadow:0 0 0 5px rgba(91,227,161,.25)}
.node.now .lab{border-color:var(--green);color:var(--green);font-weight:600}
.flow{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}
.flow div{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px 14px;flex:1;min-width:130px}
.tl{border-left:3px solid var(--teal);padding-left:18px;margin:10px 0 10px 6px}
.tl div{margin-bottom:12px}.tl b{color:var(--teal)}
.big{font-size:2rem;font-weight:700;color:var(--green)}
.note{font-size:.85rem;color:var(--mute)}
.keep{background:#1B3F36;border:1px solid #2F7A62;border-radius:14px;padding:16px 20px}
label{font-weight:600;display:block;margin:14px 0 6px}
input[type=text]{width:100%;padding:10px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font-size:1rem}
.dash-dropdown,.Select-control,.Select-menu-outer,.Select-value-label{color:#111}
.rc-slider-mark-text,.dash-slider-mark{color:var(--mute)!important}
table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}
.foot{border-top:1px solid var(--line);margin-top:26px;padding-top:12px;font-size:.85rem;color:var(--mute)}
.foot a{margin-right:12px}
@media(max-width:860px){.shell{flex-direction:column}.side{width:100%;height:auto;position:static}
 .content{padding:20px 16px}h1{font-size:1.8rem}.node .lab{font-size:.7rem}}
"""

app = Dash(__name__, suppress_callback_exceptions=True, title="Dans la peau d'une requête")
app.index_string = f"""<!DOCTYPE html><html lang="fr"><head>{{%metas%}}<title>{{%title%}}</title>
{{%favicon%}}{{%css%}}<style>{CSS}</style></head><body>{{%app_entry%}}
<footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer></body></html>"""


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def fr(x, d=2):
    """Nombre au format français."""
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def sci(x):
    e = int(math.floor(math.log10(x)))
    return f"{x / 10 ** e:.1f}".replace(".", ",") + " × 10" + str(e).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))


def badge(kind):
    return html.Span(STATUS_LABEL[kind], className=f"badge {kind}")


def srow(title, kind, text):
    return html.Div([html.Div([html.B(title), html.Small(text)]), badge(kind)], className="srow")


def fig_style(fig, h=340):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=44, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#E8F0FA"))
    fig.update_xaxes(gridcolor="#27406A")
    fig.update_yaxes(gridcolor="#27406A")
    return fig


def energy_wh(model_key, words_out):
    """Énergie estimée (Wh) pour une réponse : HYPOTHÈSE pédagogique, pas une mesure."""
    m = MODELS[model_key]
    return m["wh1k"] * (words_out * 1.35) / 1000 * m["mult"]


def next_link(href, label):
    return html.Div(dcc.Link(f"Suite : {label}", href=href, className="btn"), style={"marginTop": "22px"})


def load_real_data(path=os.path.join("data", "ai_energy_score.csv")):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------- #
# Page 1 : Comprendre l'IA
# --------------------------------------------------------------------------- #
def page_comprendre():
    return html.Div([
        html.Div([html.H1(["Une requête. Un voyage. ", html.Span("Des ressources.")]),
                  html.P("Suivez le parcours d'une question, de votre écran aux serveurs, puis jusqu'à la réponse.",
                         className="sub"),
                  dcc.Link("Devenir une requête", href="/voyage", className="btn")], className="hero"),
        html.H2("Qu'est-ce que l'IA ?"),
        html.Div([
            html.Div([html.H3("IA à règles"), html.P("Un humain écrit chaque règle. Fiable mais rigide.")], className="panel"),
            html.Div([html.H3("Apprentissage automatique"),
                      html.P("Le programme trouve les règles à partir d'exemples (filtre anti-spam).")], className="panel"),
            html.Div([html.H3("IA générative"),
                      html.P("Un grand modèle apprend la structure du langage ou des images, puis crée du contenu.")],
                     className="panel"),
        ], className="grid"),
        html.Div([html.H3("L'idée clé"),
                  html.P("Un modèle de langage prédit le prochain morceau de mot (un token), encore et encore. "
                         "Chaque prédiction exige des milliards de multiplications sur des puces spécialisées : "
                         "c'est la source de la consommation d'énergie.")], className="panel"),
        html.H2("Comment tout a explosé"),
        html.Div([
            html.Div([html.B("1956 "), "Le terme « intelligence artificielle » naît à Dartmouth."]),
            html.Div([html.B("2012 "), "AlexNet prouve la puissance du deep learning sur GPU."]),
            html.Div([html.B("2017 "), "L'architecture Transformer (Google) devient la base des modèles actuels."]),
            html.Div([html.B("2020 "), "GPT-3 : 175 milliards de paramètres, preuve que « plus grand » ouvre de nouvelles capacités."]),
            html.Div([html.B("2022 "), "ChatGPT rend l'IA générative grand public."]),
            html.Div([html.B("2024-25 "), "Modèles de raisonnement, multimodaux, agents : meilleurs, mais souvent plus gourmands."]),
        ], className="tl"),
        next_link("/voyage", "le voyage d'une requête"),
    ])


# --------------------------------------------------------------------------- #
# Page 2 : Le voyage d'une requête (immersif)
# --------------------------------------------------------------------------- #
def page_voyage():
    return html.Div([
        html.H1("Le voyage d'une requête"),
        html.P("Écrivez votre question, choisissez un modèle, puis avancez étape par étape : vous êtes la requête.",
               className="sub"),
        html.Div([
            html.Label("Votre question", htmlFor="q-text"),
            dcc.Input(id="q-text", type="text", value="Explique-moi la photosynthèse", debounce=False),
            html.Div([
                html.Div([html.Label("Modèle utilisé"),
                          dcc.Dropdown(id="q-model", options=[{"label": v["label"], "value": k} for k, v in MODELS.items()],
                                       value="moyen", clearable=False)]),
                html.Div([html.Label("Longueur de la réponse"),
                          dcc.Dropdown(id="q-len", options=[{"label": "Courte (≈ 100 mots)", "value": 100},
                                                            {"label": "Moyenne (≈ 400 mots)", "value": 400},
                                                            {"label": "Longue (≈ 1 000 mots)", "value": 1000}],
                                       value=400, clearable=False)]),
            ], className="grid"),
            html.Div([html.Button("▶ Lancer le voyage", id="btn-start", className="btn"),
                      html.Button("◀ Étape précédente", id="btn-prev", className="btn ghost"),
                      html.Button("Étape suivante ▶", id="btn-next", className="btn")], style={"marginTop": "14px"}),
        ], className="panel"),
        html.Div(id="journey-line"),
        html.Div(id="journey-detail"),
    ])


@app.callback(Output("step", "data"), Input("btn-start", "n_clicks"), Input("btn-next", "n_clicks"),
              Input("btn-prev", "n_clicks"), State("step", "data"), prevent_initial_call=True)
def move(_s, _n, _p, step):
    t = ctx.triggered_id
    if t == "btn-start":
        return 0
    if t == "btn-next":
        return min((step if step is not None else -1) + 1, 5)
    return max((step if step is not None else 0) - 1, 0)


def timeline(step):
    nodes = []
    for i, (ico, lab) in enumerate(STAGES):
        cls = "done" if step > i else "now" if step == i else "todo"
        nodes.append(html.Div([html.Div(ico, className="ico"), html.Div(lab, className="lab"),
                               html.Div(html.Div("✓" if cls == "done" else str(i + 1), className="dot"),
                                        className="dotrow")], className=f"node {cls}"))
    return html.Div(nodes, className="tline")


@app.callback(Output("journey-line", "children"), Output("journey-detail", "children"),
              Input("step", "data"), Input("q-text", "value"), Input("q-model", "value"), Input("q-len", "value"))
def render_journey(step, text, model_key, words_out):
    step = -1 if step is None else step
    text = (text or "").strip() or "Explique-moi la photosynthèse"
    m = MODELS[model_key]
    tok_in = max(1, round(len(text.split()) * 1.35))
    tok_out = round(words_out * 1.35)
    gen = tok_out * m["mult"]
    flops = 2 * m["params"] * (tok_in + gen)
    wh = energy_wh(model_key, words_out)

    if step < 0:
        return timeline(-1), html.Div(html.P("Cliquez sur « Lancer le voyage » : votre question devient une requête."),
                                      className="panel")

    if step == 0:
        body = [html.H2(["1. Votre question", badge("mesure")]),
                html.P(f"« {text} »"),
                html.P(f"Taille du texte : {len(text.encode('utf-8'))} octets, soit environ {tok_in} tokens "
                       "(estimation : un token vaut en moyenne 0,75 mot). C'est minuscule : l'envoi de la question "
                       "ne coûte presque rien. Le coût vient de ce qui se passe ensuite.")]
    elif step == 1:
        body = [html.H2(["2. Le réseau", badge("inconnu")]),
                html.P("Votre question est chiffrée (HTTPS), part de votre box, traverse les réseaux de l'opérateur "
                       "et des points d'échange, puis arrive chez le fournisseur du service, en quelques dizaines "
                       "de millisecondes."),
                html.P("Part du réseau dans l'énergie totale d'une requête : rarement mesurée de façon séparée. "
                       "Nous ne donnons donc pas de chiffre.", className="note")]
    elif step == 2:
        body = [html.H2(["3. Le centre de données", badge("estime")]),
                html.P("Un répartiteur de charge choisit un serveur équipé de GPU disponible. Le bâtiment consomme "
                       "de l'électricité pour les serveurs, mais aussi pour le refroidissement et la distribution."),
                html.P("Cet « surcoût » se mesure avec le PUE (Power Usage Effectiveness) : un PUE de 1,2 signifie "
                       "20 % d'énergie en plus de celle des serveurs. Selon les sites, on rencontre des valeurs "
                       "d'environ 1,1 (grands acteurs) à 1,6 (moyenne du secteur selon Uptime Institute).",
                       className="note")]
    elif step == 3:
        body = [html.H2(["4. Le calcul du modèle", badge("estime")]),
                html.P(m["label"]),
                html.Div([html.Div([html.Div(sci(flops), className="big"),
                                    html.P("opérations à virgule flottante (règle approchée : 2 × paramètres × tokens). "
                                           "Estimation de calcul, pas une mesure d'énergie.")], className="panel"),
                          html.Div([html.Div(f"{gen} tokens", className="big"),
                                    html.P("générés" + (" (dont une grande part de « réflexion » cachée, ×10 supposé)"
                                                        if m["mult"] > 1 else ", un par un, chacun relançant le calcul."))],
                                   className="panel")], className="grid")]
    elif step == 4:
        body = [html.H2(["5. La réponse", badge("estime")]),
                html.P(f"≈ {words_out} mots reviennent sur votre écran, soit {tok_out} tokens visibles."),
                html.Div([html.Div([html.Div(f"≈ {fr(wh)} Wh", className="big"),
                                    html.P(f"énergie estimée (fourchette plausible : {fr(wh / 3)} à {fr(wh * 3)} Wh). "
                                           "Hypothèse pédagogique, voir « Comparer » pour les valeurs publiées.")],
                                   className="panel"),
                          html.Div([html.Div(f"{fr(wh * 6, 1)} min", className="big"),
                                    html.P("d'ampoule LED de 10 W allumée pour la même énergie.")], className="panel"),
                          html.Div([html.Div(f"{fr(wh / 1000 * CO2_G_PER_KWH['France'], 3)} g CO₂", className="big"),
                                    html.P(f"avec un mix électrique français (≈ {CO2_G_PER_KWH['France']} g/kWh) ; "
                                           f"≈ {fr(wh / 1000 * CO2_G_PER_KWH['Monde'], 3)} g avec le mix mondial.")],
                                   className="panel")], className="grid"),
                html.P(["Eau consommée par le refroidissement : ", badge("inconnu"),
                        " peu d'acteurs la publient par requête."], className="note")]
    else:
        names = [v["short"] for v in MODELS.values()]
        vals = [energy_wh(k, words_out) for k in MODELS]
        fig = go.Figure(go.Bar(x=names, y=vals, text=[f"{fr(v)} Wh" for v in vals], textposition="outside",
                               marker_color=[GREEN if k == model_key else "#4C6590" for k in MODELS]))
        fig.update_layout(title="Votre requête, quatre choix de modèle (estimation, hypothèse pédagogique)")
        fig.update_yaxes(title="Wh", range=[0, max(vals) * 1.25])
        body = [html.H2("Bilan du voyage"),
                html.P("Votre requête a mobilisé un réseau, un bâtiment rempli de GPU, du refroidissement et de "
                       "l'électricité. Le choix du modèle et la longueur de la réponse sont les deux leviers "
                       "que vous contrôlez."),
                dcc.Graph(figure=fig_style(fig, 330), config={"displayModeBar": False}),
                html.Div([html.B("À retenir : "), "si un petit modèle suffit, c'est le choix le plus sobre. "
                          "Le mode raisonnement se garde pour les problèmes qui le méritent."], className="keep"),
                dcc.Link("Voir les ressources derrière le voyage", href="/ressources", className="btn")]
    return timeline(step), html.Div(body, className="panel")


# --------------------------------------------------------------------------- #
# Page 3 : Les ressources
# --------------------------------------------------------------------------- #
def page_ressources():
    fig = go.Figure(go.Bar(x=["2024", "2030 (projection)"], y=[415, 945], marker_color=[TEAL, AMBER],
                           text=["≈ 415 TWh", "≈ 945 TWh"], textposition="outside"))
    fig.update_layout(title="Électricité des data centers dans le monde (IEA, tous usages)")
    fig.update_yaxes(title="TWh par an", range=[0, 1100])
    return html.Div([
        html.H1("Les ressources derrière l'écran"),
        html.P("L'IA paraît immatérielle, mais repose sur des bâtiments, des puces, de l'électricité et de l'eau.",
               className="sub"),
        html.Div([html.Div("Requête"), html.Div("Réseau"), html.Div("Serveurs GPU"),
                  html.Div("Refroidissement"), html.Div("Électricité + eau")], className="flow"),
        html.Div([html.H2("Ce qu'on peut mesurer"),
                  srow("Énergie des GPU", "mesure", "Les puces exposent leur puissance : un laboratoire peut la mesurer pour un modèle donné."),
                  srow("Émissions de CO₂", "estime", "Elles dépendent du mix électrique du lieu et de l'heure : on les estime."),
                  srow("Eau de refroidissement", "inconnu",
                       "Google a déclaré environ 0,26 mL par requête médiane en 2025 ; la plupart des acteurs ne publient rien."),
                  srow("Fabrication des puces et serveurs", "inconnu", "Impact réel, rarement ventilé par requête.")],
                 className="panel"),
        dcc.Graph(figure=fig_style(fig, 340), config={"displayModeBar": False}),
        html.P("Les data centers pèsent environ 1,5 % de l'électricité mondiale en 2024 selon l'IEA, "
               "avec une croissance tirée par l'IA.", className="note"),
        next_link("/comparer", "comparer les modèles"),
    ])


# --------------------------------------------------------------------------- #
# Page 4 : Comparer les modèles
# --------------------------------------------------------------------------- #
def page_comparer():
    fig = go.Figure(go.Bar(
        y=[r[0] for r in REFERENCES], x=[r[1] for r in REFERENCES], orientation="h",
        marker_color=[STATUS_COLOR[r[2]] for r in REFERENCES],
        text=[f"{fr(r[1], 3 if r[1] < 1 else 1)} Wh" for r in REFERENCES], textposition="outside",
        customdata=[[STATUS_LABEL[r[2]], r[3]] for r in REFERENCES],
        hovertemplate="%{y}<br>%{x} Wh<br>%{customdata[0]} : %{customdata[1]}<extra></extra>"))
    fig.update_xaxes(type="log", title="Wh par génération (échelle logarithmique)", range=[-2, 3.8])
    fig.update_layout(title="Valeurs publiées : énergie par génération (vert = mesuré, orange = estimé)")
    rows = load_real_data()
    if rows:
        table = html.Table([html.Thead(html.Tr([html.Th(c) for c in ("Modèle", "Tâche", "Wh / 1000", "Statut", "Source")])),
                            html.Tbody([html.Tr([html.Td(r.get(k, "")) for k in
                                                 ("modele", "tache", "wh_pour_1000", "statut", "source")]) for r in rows])])
        real = html.Div([html.H3("Vos données réelles (data/ai_energy_score.csv)"), table], className="panel")
    else:
        real = html.Div([html.H3(["Données par modèle", badge("inconnu")]),
                         html.P("Aucun fichier data/ai_energy_score.csv trouvé. Téléchargez les résultats d'AI Energy Score "
                                "ou de Compar:IA, ajoutez-les en CSV (modele, tache, wh_pour_1000, source, statut) : "
                                "ils s'afficheront ici, sans modifier le code. Nous n'inventons pas de mesure par modèle.")],
                        className="panel")
    return html.Div([
        html.H1("Comparer les modèles"),
        dcc.Graph(figure=fig_style(fig, 380), config={"displayModeBar": False}),
        html.P("Ces valeurs viennent de protocoles différents : elles donnent des ordres de grandeur, pas un classement.",
               className="note"),
        real,
        html.Div([
            html.H2("Explorez un scénario"),
            html.Div([
                html.Div([
                    html.Label("1. Longueur de réponse (mots)"),
                    dcc.Slider(id="sc-words", min=50, max=1500, step=50, value=500,
                               marks={50: "50", 500: "500", 1000: "1000", 1500: "1500"}),
                    html.Label("Nombre de requêtes par mois"),
                    dcc.Slider(id="sc-req", min=10, max=5000, step=10, value=1000,
                               marks={10: "10", 1000: "1 000", 3000: "3 000", 5000: "5 000"}),
                    html.Label("2. Choisissez un modèle"),
                    dcc.Dropdown(id="sc-model", options=[{"label": v["label"], "value": k} for k, v in MODELS.items()],
                                 value="moyen", clearable=False),
                    html.Button("▶ Lancer la simulation", id="sc-go", className="btn", style={"marginTop": "14px"}),
                ]),
                html.Div(id="sc-out"),
            ], className="grid"),
            html.P("Simulation fondée sur des hypothèses pédagogiques proportionnelles à la taille du modèle.",
                   className="note"),
        ], className="panel"),
        next_link("/agir", "agir autrement"),
    ])


@app.callback(Output("sc-out", "children"), Input("sc-go", "n_clicks"), State("sc-words", "value"),
              State("sc-req", "value"), State("sc-model", "value"))
def scenario(_n, words, req, model_key):
    wh = energy_wh(model_key, words)
    kwh_month = wh * req / 1000
    names = [v["short"] for v in MODELS.values()]
    vals = [energy_wh(k, words) * req / 1000 for k in MODELS]
    fig = go.Figure(go.Bar(x=names, y=vals, text=[f"{fr(v)} kWh" for v in vals], textposition="outside",
                           marker_color=[GREEN if k == model_key else "#4C6590" for k in MODELS]))
    fig.update_layout(title="kWh par mois, selon le modèle")
    fig.update_yaxes(range=[0, max(vals) * 1.3])
    return html.Div([
        html.P([html.B(f"≈ {fr(wh)} Wh"), " par requête ; ", html.B(f"{fr(kwh_month)} kWh"), " par mois ; ",
                html.B(f"{fr(kwh_month * 12)} kWh"), " par an."]),
        html.P(f"CO₂ par an : ≈ {fr(kwh_month * 12 * CO2_G_PER_KWH['France'], 0)} g (mix français) à "
               f"{fr(kwh_month * 12 * CO2_G_PER_KWH['Monde'], 0)} g (mix mondial)."),
        dcc.Graph(figure=fig_style(fig, 260), config={"displayModeBar": False}),
    ])


# --------------------------------------------------------------------------- #
# Page 5 : Agir autrement
# --------------------------------------------------------------------------- #
def page_agir():
    return html.Div([
        html.H1("Agir autrement"),
        html.P("Sans culpabiliser : quelques choix suffisent à réduire l'impact d'un usage.", className="sub"),
        html.Div([
            html.Div([html.H3("Le plus petit modèle suffisant"),
                      html.P("Correction, reformulation, extraction : un petit modèle fait très bien l'affaire.")], className="panel"),
            html.Div([html.H3("Un prompt précis"),
                      html.P("Moins d'allers-retours, donc moins de calculs.")], className="panel"),
            html.Div([html.H3("Une réponse courte"),
                      html.P("« En 5 lignes » : l'énergie suit la longueur générée.")], className="panel"),
            html.Div([html.H3("Le raisonnement à bon escient"),
                      html.P("Réservez-le aux problèmes difficiles, il génère beaucoup de tokens cachés.")], className="panel"),
            html.Div([html.H3("Sans IA quand elle suffit"),
                      html.P("Une calculatrice, un dictionnaire ou une recherche classique suffisent parfois.")], className="panel"),
            html.Div([html.H3("Ne pas générer en double"),
                      html.P("Images et vidéos coûtent beaucoup plus que le texte : évitez les essais inutiles.")], className="panel"),
        ], className="grid"),
        html.Div([html.H2("Ce que l'on ne sait pas encore"),
                  srow("Énergie d'un modèle propriétaire précis", "inconnu", "Rarement publiée par les éditeurs."),
                  srow("Eau et fabrication par requête", "inconnu", "Peu de données comparables."),
                  srow("Valeurs par type de tâche", "estime", "Disponibles pour certains modèles ouverts (AI Energy Score).")],
                 className="panel"),
        html.Div([html.B("À retenir : "), "l'IA générative mobilise des ressources réelles. En choisissant un modèle "
                  "adapté à votre besoin et en limitant les requêtes inutiles, vous réduisez son impact."], className="keep"),
    ])


# --------------------------------------------------------------------------- #
# Layout global et routage
# --------------------------------------------------------------------------- #
PAGES = [("/", "🏠  Comprendre l'IA", page_comprendre), ("/voyage", "🔀  Le voyage d'une requête", page_voyage),
         ("/ressources", "🗄️  Les ressources", page_ressources), ("/comparer", "⚖️  Comparer les modèles", page_comparer),
         ("/agir", "🌿  Agir autrement", page_agir)]

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="step", data=-1),
    html.Div([
        html.Nav([html.Div("DANS LA PEAU D'UNE REQUÊTE", className="brand"),
                  html.Div("Comprendre • Explorer • Agir", className="tag"),
                  html.Div(id="menu"),
                  html.Div("💡 Une IA plus sobre, c'est possible. En comprenant son impact, on peut faire des choix "
                           "plus responsables.", className="tipbox")], className="side"),
        html.Main([html.Div(id="page"),
                   html.Div([html.Div(["Nos sources : "] + [html.A(n, href=u, target="_blank", rel="noopener") for n, u in SOURCES]),
                             html.Div("Les chiffres sont indicatifs et dépendent des sources et des méthodologies. "
                                      "Statuts : Mesuré, Estimé, Inconnu.")], className="foot")], className="content"),
    ], className="shell"),
])


@app.callback(Output("page", "children"), Output("menu", "children"), Input("url", "pathname"))
def router(path):
    path = path or "/"
    builder = next((b for p, _, b in PAGES if p == path), page_comprendre)
    menu = [dcc.Link(lab, href=p, className="nav on" if p == path else "nav") for p, lab, _ in PAGES]
    return builder(), menu


if __name__ == "__main__":
    app.run(debug=True)