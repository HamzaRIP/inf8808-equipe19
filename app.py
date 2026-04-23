import dash
from dash import dcc, html, Input, Output, State, ALL
import pandas as pd

from components.v1_bar_chart import render as v1
from components.v2_dumbbell   import render as v2
from components.v3_bubble     import render as v3, V3_X_OPTIONS, V3_Y_OPTIONS, V3_SIZE_OPTIONS
from components.v4_chord      import render as v4
from components.v5_slope      import render as v5

THEME = 'dark'

# ── Data ───────────────────────────────────────────────────────────────────────
df = pd.read_csv('spotify_songs.csv')
df['year'] = pd.to_datetime(df['track_album_release_date'], errors='coerce').dt.year
df = df.dropna(subset=['year', 'track_popularity'])
df['year'] = df['year'].astype(int)

GENRES   = sorted(df['playlist_genre'].dropna().unique().tolist())
MIN_YEAR = int(df['year'].min())
MAX_YEAR = int(df['year'].max())

# ── App ────────────────────────────────────────────────────────────────────────
app    = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = 'Spotify Factors — Équipe 19'


# ── Textes explicatifs (un par visualisation) ──────────────────────────────────
def _desc(title, paras, bullets=None):
    """Génère un panneau texte structuré."""
    children = [html.H3(title, className='desc-title')]
    for p in paras:
        children.append(html.P(p, className='desc-para'))
    if bullets:
        children.append(html.Ul([html.Li(b) for b in bullets], className='desc-list'))
    return children


VIZ_DESCRIPTIONS = {
    'v1': _desc(
        'Corrélations audio ↔ popularité',
        [
            'Cette visualisation présente les corrélations entre différentes '
            'caractéristiques audio des chansons et leur score de popularité sur Spotify. '
            'Chaque barre correspond à un attribut audio (danceability, énergie, tempo…) '
            'et sa longueur indique la force de la relation avec la popularité.',

            "L'axe horizontal représente le coefficient de corrélation de Pearson, "
            'qui varie entre −1 et 1. Une valeur positive indique qu\'une augmentation '
            "de l'attribut est associée à une popularité plus élevée ; une valeur négative "
            'indique la relation inverse.',

            'Les barres vertes (droite du zéro) signalent des corrélations positives, '
            'les barres grises (gauche) des corrélations négatives. '
            'Plus une barre est éloignée de zéro, plus la relation est forte.',

            'Cette visualisation permet d\'identifier rapidement quels attributs audio '
            'sont les plus associés à la popularité des morceaux.',
        ],
    ),
    'v2': _desc(
        'Profil audio : populaires vs impopulaires',
        [
            'Cette visualisation compare les caractéristiques audio moyennes des chansons '
            'populaires et impopulaires sur Spotify. Chaque ligne correspond à un attribut '
            'audio, et les points représentent les valeurs moyennes pour chaque groupe.',

            "L'axe horizontal indique la valeur normalisée de chaque attribut (0 à 1). "
            'Plus un point est à droite, plus la caractéristique est présente dans les '
            'chansons du groupe concerné.',

            'Les points verts représentent les chansons populaires (≥ Q75), '
            'les points gris les chansons impopulaires (≤ Q25). '
            "L'écart entre les deux points sur une même ligne mesure la différence "
            'entre les deux groupes.',

            'Les valeurs affichées à droite indiquent cette différence : '
            'un signe + signifie que l\'attribut est plus présent dans les chansons populaires.',

            'On observe notamment une plus forte danceability, une valence légèrement '
            'plus élevée et une plus faible instrumentalité dans les morceaux populaires, '
            'suggérant une présence vocale plus importante.',
        ],
    ),
    'v3': _desc(
        'Signature audio par sous-genre',
        [
            'Ce nuage de bulles représente les sous-genres musicaux selon leurs '
            'caractéristiques audio moyennes. Chaque bulle correspond à un sous-genre, '
            'sa taille reflète une troisième dimension (valence, énergie ou effectif), '
            'et sa couleur indique le genre musical parent.',

            'Les axes X et Y, configurables via les menus déroulants, représentent '
            'la valeur moyenne de l\'attribut sélectionné pour l\'ensemble des titres '
            'du sous-genre. L\'algorithme de placement écarte les bulles qui se '
            'chevauchent tout en conservant leur position relative sur les axes.',

            'Le curseur Top N limite l\'affichage aux N sous-genres les plus populaires, '
            'ce qui réduit la surcharge visuelle et accélère le rendu.',

            'Cette visualisation permet d\'explorer comment les sous-genres se '
            'positionnent selon différentes caractéristiques audio et d\'identifier '
            'des regroupements ou des tendances entre genres proches.',
        ],
        bullets=[
            'Axe X / Axe Y : choisissez n\'importe quelle caractéristique audio',
            'Taille : valence, énergie, danceability ou effectif (nombre de titres)',
            'Top N : nombre de sous-genres affichés (5 à 24)',
        ],
    ),
    'v4': _desc(
        'Connexions entre genres musicaux',
        [
            'Ce diagramme à cordes montre les connexions entre les différents genres '
            'musicaux des chansons dans la période choisie.',

            'Chaque arc de cercle correspond à un genre musical ; sa taille est '
            'proportionnelle à la part de titres qu\'il représente par rapport au '
            'nombre de titres total.',

            'Chaque ruban reliant deux genres représente les titres partageant ces '
            'deux styles musicaux. Plus le ruban est épais, plus ces deux genres '
            'ont des titres en commun.',

            'En survolant un arc, on obtient le nombre de titres appartenant à ce '
            'genre et sa part dans l\'ensemble sélectionné. En survolant un ruban, '
            'on voit le nombre de titres partagés et la proportion dans chacun des '
            'deux genres.',

            'On peut ainsi identifier quels genres partagent le plus de chansons, '
            'mettant en lumière les ponts stylistiques et les tendances '
            'de genres croisés favorisant la popularité.',
        ],
    ),
    'v5': _desc(
        'Évolution temporelle des attributs audio',
        [
            'Cette visualisation présente l\'évolution de huit caractéristiques audio '
            'des chansons Spotify au fil de trois époques musicales calculées '
            'automatiquement selon la période sélectionnée.',

            'Chaque ligne correspond à une caractéristique audio (énergie, danceability, '
            'valence…) et sa trajectoire illustre comment cet attribut a évolué en '
            'moyenne d\'une époque à l\'autre. Les valeurs sont normalisées entre 0 et 1.',

            "L'axe vertical représente la valeur moyenne normalisée de chaque "
            'caractéristique. Une ligne montante indique une progression au fil du temps, '
            'une ligne descendante une diminution.',

            'Les trois époques couvrent respectivement le début, le milieu et la fin '
            'de la plage temporelle choisie. Modifier le filtre Période ou sélectionner '
            'un genre recalcule automatiquement les époques et les moyennes.',

            'Cette visualisation permet d\'identifier quels attributs audio ont gagné '
            'ou perdu en importance au fil des décennies, et comment le profil sonore '
            'd\'un genre a évolué dans le temps.',
        ],
    ),
}


def genre_buttons():
    """Boutons genre custom (tous activés par défaut = classe 'genre-btn active')."""
    return html.Div(
        className='genre-checklist',
        children=[
            html.Button(
                g.upper(),
                id={'type': 'genre-btn', 'index': g},
                className='genre-btn active',
                n_clicks=0,
            )
            for g in GENRES
        ],
    )


def viz_card(card_id, graph_id, fullscreen_id, description=None, extra=None):
    """Carte visualisation avec panneau texte latéral (visible en mode zoom)."""
    return html.Div(id=card_id, className='viz-card', children=[
        html.Div(className='viz-label', children=[
            html.Button('⛶', id=fullscreen_id, className='fullscreen-btn', n_clicks=0),
        ]),
        *([extra] if extra else []),
        html.Div(className='viz-body', children=[
            dcc.Graph(id=graph_id, className='viz-graph', config={'displayModeBar': False}),
            html.Div(
                className='viz-text-panel',
                children=description or [],
            ),
        ]),
    ])


v3_controls = html.Div(className='v3-controls', children=[
    html.Div([
        html.Label('Axe X', className='control-label'),
        dcc.Dropdown(id='v3-x', options=V3_X_OPTIONS,
                     value='acousticness_sqrt', clearable=False, className='v3-dropdown'),
    ]),
    html.Div([
        html.Label('Axe Y', className='control-label'),
        dcc.Dropdown(id='v3-y', options=V3_Y_OPTIONS,
                     value='track_popularity', clearable=False, className='v3-dropdown'),
    ]),
    html.Div([
        html.Label('Taille', className='control-label'),
        dcc.Dropdown(id='v3-size', options=V3_SIZE_OPTIONS,
                     value='valence', clearable=False, className='v3-dropdown'),
    ]),
    html.Div([
        html.Label('Top N', className='control-label'),
        dcc.Slider(id='v3-topn', min=5, max=24, step=1, value=18,
                   marks={5: '5', 12: '12', 18: '18', 24: '24'},
                   className='v3-slider'),
    ]),
])

app.layout = html.Div(id='dashboard', className='dashboard', children=[

    html.Header(id='main-header', className='header', children=[
        html.Div(className='header-left', children=[
            html.Span('♫', className='logo'),
            html.Div([
                html.H1('Spotify Factors'),
                html.P('INF8808 · Équipe 19'),
            ]),
        ]),
        html.Div(className='controls', children=[
            html.Div(className='control-group', children=[
                html.Label('Genre', className='control-label'),
                genre_buttons(),
            ]),
            html.Div(className='control-group', children=[
                html.Label(id='year-label', className='control-label'),
                dcc.RangeSlider(
                    id='year-filter',
                    min=MIN_YEAR, max=MAX_YEAR,
                    value=[MIN_YEAR, MAX_YEAR],
                    marks={y: str(y) for y in range(MIN_YEAR, MAX_YEAR + 1, 10)},
                    tooltip={'placement': 'bottom', 'always_visible': False},
                    updatemode='mouseup',
                    className='year-slider',
                ),
            ]),
            html.Div(id='data-count', className='data-count'),
        ]),
    ]),

    html.Main(className='grid', children=[
        viz_card('card-v1', 'v1', 'fullscreen-v1',
                 description=VIZ_DESCRIPTIONS['v1']),
        viz_card('card-v2', 'v2', 'fullscreen-v2',
                 description=VIZ_DESCRIPTIONS['v2']),
        viz_card('card-v3', 'v3', 'fullscreen-v3',
                 description=VIZ_DESCRIPTIONS['v3'], extra=v3_controls),
        viz_card('card-v4', 'v4', 'fullscreen-v4',
                 description=VIZ_DESCRIPTIONS['v4']),
        viz_card('card-v5', 'v5', 'fullscreen-v5',
                 description=VIZ_DESCRIPTIONS['v5']),
    ]),

    html.Button('✕', id='close-fullscreen', className='close-fullscreen-btn',
                n_clicks=0, style={'display': 'none'}),

    # Store : liste des genres actifs
    dcc.Store(id='active-genres', data=GENRES),
])


# ── Callback : toggle individuel d'un bouton genre ────────────────────────────
@app.callback(
    Output({'type': 'genre-btn', 'index': ALL}, 'className'),
    Output('active-genres', 'data'),
    Input({'type': 'genre-btn', 'index': ALL}, 'n_clicks'),
    State({'type': 'genre-btn', 'index': ALL}, 'className'),
    State({'type': 'genre-btn', 'index': ALL}, 'id'),
    prevent_initial_call=True,
)
def toggle_genre(n_clicks_list, class_list, id_list):
    triggered = dash.ctx.triggered_id
    if triggered is None:
        raise dash.exceptions.PreventUpdate

    clicked_genre = triggered['index']
    new_classes = []
    for cls, id_obj in zip(class_list, id_list):
        if id_obj['index'] == clicked_genre:
            new_cls = 'genre-btn' if 'active' in cls else 'genre-btn active'
        else:
            new_cls = cls
        new_classes.append(new_cls)

    active = [id_obj['index'] for cls, id_obj in zip(new_classes, id_list)
              if 'active' in cls]
    return new_classes, active


# ── Callback : graphes principaux ─────────────────────────────────────────────
@app.callback(
    Output('v1', 'figure'),
    Output('v2', 'figure'),
    Output('v4', 'figure'),
    Output('v5', 'figure'),
    Output('data-count', 'children'),
    Output('year-label',  'children'),
    Input('active-genres', 'data'),
    Input('year-filter',   'value'),
)
def update_main(genres, year_range):
    genres = genres or GENRES
    filtered = df[
        df['playlist_genre'].isin(genres) &
        df['year'].between(year_range[0], year_range[1])
    ]
    count      = f'{len(filtered):,} titres'
    year_label = f'Période : {year_range[0]} – {year_range[1]}'
    return v1(filtered, THEME), v2(filtered, THEME), v4(filtered, THEME), v5(filtered, THEME), count, year_label


# ── Callback : V3 ─────────────────────────────────────────────────────────────
@app.callback(
    Output('v3', 'figure'),
    Input('active-genres', 'data'),
    Input('year-filter',   'value'),
    Input('v3-x',    'value'),
    Input('v3-y',    'value'),
    Input('v3-size', 'value'),
    Input('v3-topn', 'value'),
)
def update_v3(genres, year_range, x_key, y_key, size_key, top_n):
    genres = genres or GENRES
    filtered = df[
        df['playlist_genre'].isin(genres) &
        df['year'].between(year_range[0], year_range[1])
    ]
    return v3(filtered, x_key, y_key, size_key, top_n, THEME)


# ── Callback : fullscreen ─────────────────────────────────────────────────────
BASE_CLASSES = ['viz-card'] * 5

@app.callback(
    Output('card-v1', 'className'),
    Output('card-v2', 'className'),
    Output('card-v3', 'className'),
    Output('card-v4', 'className'),
    Output('card-v5', 'className'),
    Output('close-fullscreen', 'style'),
    Output('main-header', 'style'),
    Input('fullscreen-v1', 'n_clicks'),
    Input('fullscreen-v2', 'n_clicks'),
    Input('fullscreen-v3', 'n_clicks'),
    Input('fullscreen-v4', 'n_clicks'),
    Input('fullscreen-v5', 'n_clicks'),
    Input('close-fullscreen', 'n_clicks'),
    prevent_initial_call=True,
)
def toggle_fullscreen(n1, n2, n3, n4, n5, n_close):
    triggered   = dash.ctx.triggered_id
    classes     = list(BASE_CLASSES)
    close_style = {'display': 'none'}
    header_style = {}

    if triggered != 'close-fullscreen':
        idx = int(triggered.split('-v')[1]) - 1
        classes[idx] += ' viz-fullscreen'
        close_style  = {'display': 'flex'}
        header_style = {'position': 'fixed', 'top': '0', 'left': '0',
                        'width': '100%', 'zIndex': '1000'}

    return *classes, close_style, header_style


if __name__ == '__main__':
    app.run(debug=True)
