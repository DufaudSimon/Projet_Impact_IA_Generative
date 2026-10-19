"""
LE VOYAGE D'UNE QUESTION : comprendre ce que consomme une IA, en 8 écrans.

Installation :  python -m pip install dash plotly
Lancement    :  python app.py   puis ouvrir http://127.0.0.1:8050

Principe : un seul chemin guidé, une idée par écran, des comparaisons du quotidien.
Les chiffres sont des ORDRES DE GRANDEUR tirés d'études publiques (voir écran final).
"""
import plotly.graph_objects as go
from dash import Dash, ctx, dcc, html, Input, Output, State

# --------------------------------------------------------------------------- #
# Données (ordres de grandeur, sources citées à l'écran)
# --------------------------------------------------------------------------- #
TASKS = {
    "faute": {"label": "Corriger une faute dans un texte", "icon": "✏️", "wh": 0.05,
              "last": "Un petit programme d'IA suffit : il réécrit votre texte, mot après mot.",
              "src": "mesure moyenne sur de petits modèles (Luccioni et al., 2023-24)"},
    "question": {"label": "Poser une question", "icon": "💬", "wh": 0.3,
                 "last": "Le programme compose la réponse mot après mot. Chaque mot demande un calcul.",
                 "src": "estimations de Google (0,24 Wh, 2025) et d'Epoch AI (≈ 0,3 Wh, 2025)"},
    "image": {"label": "Créer une image", "icon": "🖼️", "wh": 3.0,
              "last": "L'IA calcule des millions de points de couleur : bien plus de travail que pour du texte.",
              "src": "mesure sur le modèle le plus gourmand testé (Luccioni et al., 2023-24)"},
    "video": {"label": "Créer une vidéo de 5 secondes", "icon": "🎬", "wh": 944.0,
              "last": "Une vidéo, ce sont des dizaines d'images à produire et à relier : le plus gros calcul de tous.",
              "src": "mesure sur un modèle ouvert (MIT Technology Review, 2025)"},
}

PREDICTIONS = {
    "Le chat dort sur le…": [("canapé", 35), ("lit", 25), ("tapis", 15), ("toit", 10), ("autre", 15)],
    "Il fait beau, allons à la…": [("plage", 40), ("montagne", 20), ("campagne", 15), ("piscine", 15), ("autre", 10)],
    "Pour faire un gâteau, il faut des…": [("œufs", 45), ("oeufs de poule", 5), ("pommes", 15), ("fraises", 10), ("autre", 25)],
}

SIZES = [  # (nom, image, poids relatif de conso — HYPOTHÈSE pédagogique)
    ("Petit modèle", "🚲", 1, "pour les tâches simples"),
    ("Modèle moyen", "🚗", 4, "pour les tâches courantes"),
    ("Très gros modèle", "🚛", 20, "pour les tâches très difficiles"),
]
DIFFICULTY = {
    "simple": ("Simple : corriger, reformuler, classer", 0),
    "moyen": ("Courante : résumer, écrire un mail, coder un petit script", 1),
    "dur": ("Difficile : analyse longue, problème complexe", 2),
}

TITLES = ["Bienvenue", "C'est quoi une IA ?", "Pourquoi tout s'est accéléré", "Le voyage d'une question",
          "Ce qu'il y a derrière", "Le bon outil pour la bonne tâche", "Et pour moi ?", "À retenir"]
LAST = len(TITLES) - 1

# --------------------------------------------------------------------------- #
# Style : clair, grand, très lisible
# --------------------------------------------------------------------------- #
CSS = """
:root{--bg:#F3F6F8;--card:#fff;--ink:#10233A;--mute:#4A5D72;--teal:#0A7F78;--tealsoft:#D9F0EE;
--amber:#F2A900;--ambersoft:#FFF1CC;--line:#D5DEE6}
*{box-sizing:border-box}
html{font-size:18px}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI",system-ui,Helvetica,Arial,sans-serif;line-height:1.65}
h1{font-size:2.5rem;line-height:1.15;margin:0 0 .5em}h2{font-size:1.9rem;line-height:1.2;margin:0 0 .5em}h3{font-size:1.15rem;margin:0 0 .3em}
p{margin:0 0 1em;max-width:62ch}
a{color:var(--teal)}
.top{max-width:900px;margin:0 auto;padding:22px 20px 0}
.brand{font-weight:700;color:var(--teal)}
.bar{display:flex;gap:6px;margin:10px 0 6px}
.seg{height:7px;flex:1;border-radius:9px;background:var(--line)}
.seg.done{background:var(--teal)}.seg.now{background:var(--amber)}
.where{color:var(--mute);font-size:.95rem}
.stage{max-width:900px;margin:14px auto;padding:0 20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:30px 34px;min-height:420px}
.lead{font-size:1.25rem;max-width:56ch}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:18px 0}
.box{background:var(--bg);border-radius:14px;padding:16px 18px}
.box .em{font-size:2rem}
.hl{background:var(--tealsoft);border-radius:14px;padding:16px 20px}
.warn{background:var(--ambersoft);border-radius:14px;padding:16px 20px}
.big{font-size:2.6rem;font-weight:700;color:var(--teal);line-height:1.1}
.nav{max-width:900px;margin:0 auto 40px;padding:0 20px;display:flex;justify-content:space-between;gap:12px}
.btn{font-size:1.1rem;font-weight:700;border-radius:12px;padding:14px 28px;cursor:pointer;border:2px solid var(--teal);
 background:var(--teal);color:#fff}
.btn.ghost{background:#fff;color:var(--teal)}
.btn:hover{filter:brightness(1.1)}
.btn:focus-visible,input:focus-visible{outline:3px solid var(--amber);outline-offset:2px}
.choice{display:block;border:2px solid var(--line);border-radius:12px;padding:12px 16px;margin:8px 0;cursor:pointer;background:#fff}
.choice:hover{border-color:var(--teal)}
.choice input{margin-right:10px;transform:scale(1.3)}
.path{border-left:4px solid var(--teal);margin:18px 0 18px 14px;padding-left:22px}
.stop{margin-bottom:16px;position:relative}
.stop::before{content:"";position:absolute;left:-31px;top:8px;width:14px;height:14px;border-radius:50%;background:var(--teal);border:3px solid #fff}
.stop:last-child::before{background:var(--amber)}
.bars div.row{display:flex;align-items:center;gap:10px;margin:8px 0}
.bars .name{width:130px;flex:none}
.bars .track{flex:1;background:var(--line);border-radius:8px;height:26px;overflow:hidden}
.bars .fill{background:var(--teal);height:100%;color:#fff;padding-left:8px;font-size:.9rem;line-height:26px;white-space:nowrap}
.small{font-size:.88rem;color:var(--mute)}
.dash-slider-mark,.rc-slider-mark-text{color:var(--mute)!important;font-size:.85rem}
@media(max-width:640px){html{font-size:16px}.card{padding:20px 18px}h1{font-size:2rem}.bars .name{width:90px}}
"""

app = Dash(__name__, suppress_callback_exceptions=True, title="Le voyage d'une question")
app.index_string = f"""<!DOCTYPE html><html lang="fr"><head>{{%metas%}}<title>{{%title%}}</title>
{{%favicon%}}{{%css%}}<style>{CSS}</style></head><body>{{%app_entry%}}
<footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer></body></html>"""


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def fr(x, d=1):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def equivalents(wh):
    """Traduit des Wh en comparaisons du quotidien (LED 10 W ; téléphone ≈ 15 Wh)."""
    sec = wh / 10 * 3600
    if sec < 90:
        led = f"{sec:.0f} secondes"
    elif sec < 7200:
        led = f"{sec / 60:.0f} minutes"
    else:
        led = f"{sec / 3600:.0f} heures"
    out = [f"une ampoule LED allumée pendant {led}"]
    if wh >= 15:
        out.append(f"{wh / 15:.0f} recharges complètes d'un téléphone")
    return out


def box(emoji, title, text):
    return html.Div([html.Div(emoji, className="em"), html.H3(title), html.P(text, style={"margin": 0})], className="box")


# --------------------------------------------------------------------------- #
# Les 8 écrans
# --------------------------------------------------------------------------- #
def s0():
    return html.Div([
        html.H1("Que se passe-t-il quand vous posez une question à une IA ?"),
        html.P("En 8 petits écrans (environ 5 minutes), vous allez suivre le voyage d'une question, "
               "de votre écran jusqu'à la réponse, et comprendre ce que cela consomme.", className="lead"),
        html.Div([html.B("Aucune connaissance nécessaire. "),
                  "Chaque écran explique une seule idée. Utilisez les boutons en bas pour avancer."], className="hl"),
    ])


def s1():
    return html.Div([
        html.H2("Une IA, c'est un programme qui devine la suite"),
        html.P("Une IA comme ChatGPT a « lu » énormément de textes. Quand vous lui écrivez, elle ne réfléchit pas "
               "comme nous : elle devine, mot après mot, quel mot a le plus de chances de venir ensuite.", className="lead"),
        html.Label("Essayez : choisissez un début de phrase", htmlFor="pred-in", style={"fontWeight": 700}),
        dcc.RadioItems(id="pred-in", options=list(PREDICTIONS), value="Le chat dort sur le…", labelClassName="choice"),
        html.Div(id="pred-out"),
        html.P("Exemple pédagogique : les pourcentages sont inventés pour illustrer, pas mesurés.", className="small"),
    ])


@app.callback(Output("pred-out", "children"), Input("pred-in", "value"))
def pred(value):
    rows = [html.Div([html.Div(w, className="name"),
                      html.Div(html.Div(f"{p} %", className="fill", style={"width": f"{p * 2}%"}), className="track")],
                     className="row") for w, p in PREDICTIONS[value]]
    return html.Div([html.P("L'IA classe les mots possibles par probabilité, puis en choisit un :"),
                     html.Div(rows, className="bars")])


def s2():
    return html.Div([
        html.H2("Pourquoi tout s'est accéléré"),
        html.P("Les IA existent depuis les années 1950. Elles sont devenues très puissantes quand trois choses "
               "se sont réunies :", className="lead"),
        html.Div([box("📚", "Beaucoup de textes", "Internet, livres, articles : de quoi apprendre à écrire."),
                  box("⚡", "Des puces très rapides", "Des processeurs (les GPU) capables de faire des milliards de calculs à la seconde."),
                  box("💡", "Une bonne idée (2017)", "Une nouvelle façon de construire ces programmes, appelée « Transformer ».")],
                 className="grid"),
        html.Div([html.B("2022 : ChatGPT. "), "En environ deux mois, il a dépassé 100 millions d'utilisateurs. "
                  "Depuis, les modèles grossissent : entre 2018 et 2020, le nombre de « réglages internes » du "
                  "modèle d'OpenAI est passé d'environ 117 millions à 175 milliards, soit 1 500 fois plus."], className="hl"),
    ])


def s3():
    return html.Div([
        html.H2("Le voyage d'une question"),
        html.P("Choisissez ce que vous demandez à l'IA. Vous allez voir où va votre demande, et ce que cela consomme.",
               className="lead"),
        dcc.RadioItems(id="task", options=[{"label": f"{t['icon']}  {t['label']}", "value": k} for k, t in TASKS.items()],
                       value="question", labelClassName="choice"),
        html.Div(id="voyage-out"),
    ])


@app.callback(Output("voyage-out", "children"), Input("task", "value"))
def voyage(key):
    t = TASKS[key]
    stops = [("💻 Votre écran", "Vous écrivez votre demande."),
             ("🌐 Internet", "Elle voyage jusqu'à un centre de données, un grand bâtiment rempli d'ordinateurs."),
             ("🏢 Le centre de données", "Des puces spécialisées se mettent au travail, avec de l'électricité."),
             ("✨ La réponse", t["last"])]
    eq = equivalents(t["wh"])
    return html.Div([
        html.Div([html.Div([html.H3(a), html.P(b, style={"margin": 0})], className="stop") for a, b in stops], className="path"),
        html.Div([html.Div(f"≈ {fr(t['wh'], 2 if t['wh'] < 1 else 1)} Wh", className="big"),
                  html.P("C'est l'énergie électrique d'environ : " + " ; ".join(eq) + "."),
                  html.P(f"Source : {t['src']}. Ordre de grandeur.", className="small", style={"margin": 0})], className="warn"),
    ])


def s4():
    return html.Div([
        html.H2("Ce qu'il y a derrière : les centres de données"),
        html.P("Votre question n'est pas traitée par votre téléphone, mais par un centre de données, parfois à des "
               "milliers de kilomètres. C'est un immense entrepôt d'ordinateurs qui fonctionnent jour et nuit.",
               className="lead"),
        html.Div([box("🔌", "De l'électricité", "Pour faire tourner les puces."),
                  box("❄️", "Du refroidissement", "Les puces chauffent beaucoup : il faut les refroidir, avec de l'air ou de l'eau."),
                  box("🧱", "Du matériel à fabriquer", "Puces, serveurs, bâtiments : leur fabrication a aussi un coût.")],
                 className="grid"),
        html.Div([html.Div("≈ 1,5 %", className="big"),
                  html.P("de l'électricité mondiale passe dans les centres de données (Agence internationale de "
                         "l'énergie, 2024). Cette part pourrait plus que doubler d'ici 2030, en partie à cause de l'IA.",
                         style={"margin": 0})], className="warn"),
        html.P("Ce qu'on ne sait pas bien : la quantité d'eau utilisée. Peu d'entreprises la publient.",
               className="small", style={"marginTop": "14px"}),
    ])


def s5():
    return html.Div([
        html.H2("Le bon outil pour la bonne tâche"),
        html.P("Il existe des IA de tailles différentes. Pour se déplacer, on ne prend pas un camion pour aller "
               "chercher du pain : c'est pareil ici.", className="lead"),
        html.Label("Votre demande est…", htmlFor="diff", style={"fontWeight": 700}),
        dcc.RadioItems(id="diff", options=[{"label": v[0], "value": k} for k, v in DIFFICULTY.items()],
                       value="simple", labelClassName="choice"),
        html.Div(id="diff-out"),
    ])


@app.callback(Output("diff-out", "children"), Input("diff", "value"))
def diff(key):
    best = DIFFICULTY[key][1]
    cards = []
    for i, (name, ico, rel, use) in enumerate(SIZES):
        style = {"border": "3px solid #0A7F78"} if i == best else {}
        cards.append(html.Div([html.Div(ico, className="em"), html.H3(name), html.P(use, style={"margin": 0}),
                               html.P(f"Consomme environ ×{rel}", className="small", style={"margin": 0}),
                               html.B("✔ Le plus adapté", style={"color": "#0A7F78"}) if i == best else ""],
                              className="box", style=style))
    saving = SIZES[2][2] // SIZES[best][2]
    msg = ("Ici, un petit modèle suffit : prendre le plus gros consommerait environ 20 fois plus pour le même résultat."
           if best == 0 else "Prendre le modèle adapté plutôt que le plus gros évite un gaspillage inutile."
           if best == 1 else "Pour une tâche difficile, un gros modèle peut se justifier. Gardez-le pour ces cas-là.")
    return html.Div([html.Div(cards, className="grid"), html.P(msg, className="lead"),
                     html.P("Les « ×1, ×4, ×20 » sont une hypothèse pédagogique (la consommation grandit avec la taille du "
                            "modèle). Les « modèles de raisonnement », qui réfléchissent longuement avant de répondre, "
                            "peuvent consommer encore plus : environ 10 fois.", className="small")])


def s6():
    return html.Div([
        html.H2("Et pour moi ?"),
        html.P("Réglez votre usage, vous verrez ce que cela représente sur une année.", className="lead"),
        html.Label("Questions écrites par jour"),
        dcc.Slider(id="u-txt", min=0, max=100, step=5, value=20, marks={0: "0", 50: "50", 100: "100"}),
        html.Label("Images créées par semaine"),
        dcc.Slider(id="u-img", min=0, max=50, step=1, value=2, marks={0: "0", 25: "25", 50: "50"}),
        html.Label("Vidéos créées par mois"),
        dcc.Slider(id="u-vid", min=0, max=10, step=1, value=0, marks={0: "0", 5: "5", 10: "10"}),
        html.Div(id="usage-out", style={"marginTop": "22px"}),
    ])


@app.callback(Output("usage-out", "children"), Input("u-txt", "value"), Input("u-img", "value"), Input("u-vid", "value"))
def usage(txt, img, vid):
    parts = {"Textes": TASKS["question"]["wh"] * txt * 365 / 1000,
             "Images": TASKS["image"]["wh"] * img * 52 / 1000,
             "Vidéos": TASKS["video"]["wh"] * vid * 12 / 1000}
    total = sum(parts.values())
    if total == 0:
        return html.Div("Ajoutez un usage avec les curseurs.", className="hl")
    top = max(parts, key=parts.get)
    fig = go.Figure(go.Bar(x=list(parts), y=list(parts.values()), text=[f"{fr(v, 2)} kWh" for v in parts.values()],
                           textposition="outside", marker_color=["#0A7F78" if k == top else "#9FB6C3" for k in parts]))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="kWh par an",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_range=[0, max(parts.values()) * 1.3])
    return html.Div([
        html.Div([html.Div(f"≈ {fr(total, 1)} kWh par an", className="big"),
                  html.P(f"soit environ {fr(total / 1, 0)} lavages en machine (≈ 1 kWh chacun). "
                         f"Le poste qui pèse le plus : {top.lower()}.", style={"margin": 0})], className="warn"),
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        html.P("Le texte pèse peu : ce sont surtout les images et les vidéos qui comptent. Ordres de grandeur, "
               "calculés avec les valeurs de l'écran 4.", className="small"),
    ])


def s7():
    return html.Div([
        html.H2("À retenir"),
        html.Div([box("🧠", "Chaque réponse a un coût", "Même invisible, elle mobilise des ordinateurs, de l'électricité et du refroidissement."),
                  box("🎯", "Le bon modèle", "Prenez le plus petit qui fait bien le travail."),
                  box("🎬", "Images et vidéos", "Elles pèsent bien plus que le texte : évitez les essais inutiles.")],
                 className="grid"),
        html.Div([html.B("Ce que l'on ne sait pas encore : "),
                  "la consommation exacte de chaque modèle commercial, l'eau utilisée et l'impact de la fabrication. "
                  "Les chiffres de ce site sont des ordres de grandeur, pas des mesures exactes."], className="warn"),
        html.P(["Sources : Luccioni et al. (2023-24), Google (2025), Epoch AI (2025), MIT Technology Review (2025), "
                "Agence internationale de l'énergie (2024). Pour aller plus loin : ",
                html.A("AI Energy Score", href="https://huggingface.co/AIEnergyScore", target="_blank", rel="noopener"),
                " et ", html.A("Compar:IA", href="https://comparia.beta.gouv.fr", target="_blank", rel="noopener"), "."],
               className="small", style={"marginTop": "14px"}),
    ])


SCREENS = [s0, s1, s2, s3, s4, s5, s6, s7]

# --------------------------------------------------------------------------- #
# Mise en page et navigation
# --------------------------------------------------------------------------- #
app.layout = html.Div([
    dcc.Store(id="step", data=0),
    html.Div([html.Div("Le voyage d'une question", className="brand"), html.Div(id="progress")], className="top"),
    html.Main(html.Div(id="screen", className="card"), className="stage"),
    html.Div([html.Button("← Précédent", id="btn-prev", className="btn ghost"),
              html.Div([html.Button("Suivant →", id="btn-next", className="btn"),
                        html.Button("↺ Recommencer", id="btn-restart", className="btn ghost",
                                    style={"display": "none"})])], className="nav"),
])


@app.callback(Output("step", "data"), Input("btn-prev", "n_clicks"), Input("btn-next", "n_clicks"),
              Input("btn-restart", "n_clicks"), State("step", "data"), prevent_initial_call=True)
def move(_p, _n, _r, step):
    t = ctx.triggered_id
    if t == "btn-restart":
        return 0
    if t == "btn-next":
        return min(step + 1, LAST)
    return max(step - 1, 0)


@app.callback(Output("screen", "children"), Output("progress", "children"), Output("btn-prev", "style"),
              Output("btn-next", "style"), Output("btn-next", "children"), Output("btn-restart", "style"),
              Input("step", "data"))
def render(step):
    segs = [html.Div(className="seg done" if i < step else "seg now" if i == step else "seg") for i in range(len(SCREENS))]
    progress = [html.Div(segs, className="bar"),
                html.Div(f"Étape {step + 1} sur {len(SCREENS)} : {TITLES[step]}", className="where")]
    label = "Commencer le voyage →" if step == 0 else "Suivant →"
    return (SCREENS[step](), progress,
            {"visibility": "hidden"} if step == 0 else {},
            {"display": "none"} if step == LAST else {}, label,
            {} if step == LAST else {"display": "none"})


if __name__ == "__main__":
    app.run(debug=True)
