import dash
from dash import dcc, html, Input, Output, State, ALL
import pandas as pd
import json

from components.v1_bar_chart import render as v1
from components.v2_dumbbell   import render as v2
from components.v3_bubble     import render as v3, V3_X_OPTIONS, V3_Y_OPTIONS, V3_SIZE_OPTIONS
from components.v4_chord      import render as v4
from components.v5_slope      import render as v5

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


def genre_buttons():
    """Boutons genre custom (tous activés par défaut = classe 'genre-btn active')."""
    return html.Div(
        className='genre-checklist',
        children=[
            html.Button(
                g.upper(),
                id={'type': 'genre-btn', 'index': g},
                className='genre-btn active',   # actif par défaut
                n_clicks=0,
            )
            for g in GENRES
        ],
    )


def viz_card(card_id, graph_id, fullscreen_id, label, questions, extra=None):
    return html.Div(id=card_id, className='viz-card', children=[
        html.Div(className='viz-label', children=[
            label,
            html.Div(className='viz-label-right', children=[
                html.Span(questions),
                html.Button('⛶', id=fullscreen_id, className='fullscreen-btn', n_clicks=0),
            ]),
        ]),
        *([extra] if extra else []),
        dcc.Graph(id=graph_id, className='viz-graph', config={'displayModeBar': False}),
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
            html.Button('☀', id='theme-toggle', className='theme-toggle', n_clicks=0),
        ]),
    ]),

    html.Main(className='grid', children=[
        viz_card('card-v1', 'v1', 'fullscreen-v1', '01 — BAR CHART CORRÉLATIONS', 'Q1 · Q4 · Q5'),
        viz_card('card-v2', 'v2', 'fullscreen-v2', '02 — DUMBBELL CHART',          'Q2 · Q3'),
        viz_card('card-v3', 'v3', 'fullscreen-v3', '03 — BUBBLE CHART',            'Q5 · Q7 · Q8', extra=v3_controls),
        viz_card('card-v4', 'v4', 'fullscreen-v4', '04 — CHORD DIAGRAM',           'Q6 · Q9 · Q10'),
        viz_card('card-v5', 'v5', 'fullscreen-v5', '05 — SLOPE CHART TEMPOREL',    'Q10–13'),
    ]),

    html.Button('✕', id='close-fullscreen', className='close-fullscreen-btn',
                n_clicks=0, style={'display': 'none'}),

    # Store : liste des genres actifs
    dcc.Store(id='active-genres', data=GENRES),
    dcc.Store(id='theme-store', data='dark'),
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
            # toggle
            new_cls = 'genre-btn' if 'active' in cls else 'genre-btn active'
        else:
            new_cls = cls
        new_classes.append(new_cls)

    active = [id_obj['index'] for cls, id_obj in zip(new_classes, id_list)
              if 'active' in cls]
    return new_classes, active


# ── Callback : theme toggle ───────────────────────────────────────────────────
@app.callback(
    Output('dashboard',    'className'),
    Output('theme-toggle', 'children'),
    Output('theme-store',  'data'),
    Input('theme-toggle',  'n_clicks'),
)
def toggle_theme(n):
    if n % 2 == 1:
        return 'dashboard light', '🌙', 'light'
    return 'dashboard', '☀', 'dark'


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
    Input('theme-store',   'data'),
)
def update_main(genres, year_range, theme):
    genres = genres or GENRES
    filtered = df[
        df['playlist_genre'].isin(genres) &
        df['year'].between(year_range[0], year_range[1])
    ]
    count      = f'{len(filtered):,} titres'
    year_label = f'Période : {year_range[0]} – {year_range[1]}'
    return v1(filtered, theme), v2(filtered, theme), v4(filtered, theme), v5(filtered, theme), count, year_label


# ── Callback : V3 ─────────────────────────────────────────────────────────────
@app.callback(
    Output('v3', 'figure'),
    Input('active-genres', 'data'),
    Input('year-filter',   'value'),
    Input('v3-x',    'value'),
    Input('v3-y',    'value'),
    Input('v3-size', 'value'),
    Input('v3-topn', 'value'),
    Input('theme-store', 'data'),
)
def update_v3(genres, year_range, x_key, y_key, size_key, top_n, theme):
    genres = genres or GENRES
    filtered = df[
        df['playlist_genre'].isin(genres) &
        df['year'].between(year_range[0], year_range[1])
    ]
    return v3(filtered, x_key, y_key, size_key, top_n, theme)


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
