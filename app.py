import dash
from dash import dcc, html, Input, Output
import pandas as pd

from components.v1_bar_chart import render as v1
from components.v2_dumbbell import render as v2
from components.v3_bubble import render as v3
from components.v4_chord import render as v4
from components.v5_slope import render as v5

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv('spotify_songs.csv')
df['year'] = pd.to_datetime(df['track_album_release_date'], errors='coerce').dt.year
df = df.dropna(subset=['year', 'track_popularity'])
df['year'] = df['year'].astype(int)

GENRES   = sorted(df['playlist_genre'].dropna().unique().tolist())
MIN_YEAR = int(df['year'].min())
MAX_YEAR = int(df['year'].max())

# ── App ───────────────────────────────────────────────────────────────────────
app  = dash.Dash(__name__)
server = app.server
app.title = 'Spotify Factors — Équipe 19'

def viz_card(card_id, graph_id, fullscreen_id, label, questions):
    return html.Div(id=card_id, className='viz-card', children=[
        html.Div(className='viz-label', children=[
            label,
            html.Div(className='viz-label-right', children=[
                html.Span(questions),
                html.Button('⛶', id=fullscreen_id, className='fullscreen-btn', n_clicks=0),
            ]),
        ]),
        dcc.Graph(id=graph_id, className='viz-graph', config={'displayModeBar': False}),
    ])

app.layout = html.Div(id='dashboard', className='dashboard', children=[

    # ── Header ────────────────────────────────────────────────────────────────
    html.Header(className='header', children=[
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
                dcc.Checklist(
                    id='genre-filter',
                    options=[{'label': g, 'value': g} for g in GENRES],
                    value=GENRES,
                    inline=True,
                    className='genre-checklist',
                    inputClassName='genre-input',
                    labelClassName='genre-label',
                ),
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

    # ── Grid ──────────────────────────────────────────────────────────────────
    html.Main(className='grid', children=[
        viz_card('card-v1', 'v1', 'fullscreen-v1', '01 — BAR CHART CORRÉLATIONS', 'Q1 · Q4 · Q5'),
        viz_card('card-v2', 'v2', 'fullscreen-v2', '02 — DUMBBELL CHART',          'Q2 · Q3'),
        viz_card('card-v3', 'v3', 'fullscreen-v3', '03 — BUBBLE CHART',            'Q5 · Q7 · Q8'),
        viz_card('card-v4', 'v4', 'fullscreen-v4', '04 — CHORD DIAGRAM',           'Q6 · Q9 · Q10'),
        viz_card('card-v5', 'v5', 'fullscreen-v5', '05 — SLOPE CHART TEMPOREL',    'Q10–13'),
    ]),

    html.Button('✕', id='close-fullscreen', className='close-fullscreen-btn',
                n_clicks=0, style={'display': 'none'}),

    # Store theme state
    dcc.Store(id='theme-store', data='dark'),
])


# ── Callback: theme toggle ────────────────────────────────────────────────────
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


# ── Callback: update figures ──────────────────────────────────────────────────
@app.callback(
    Output('v1', 'figure'),
    Output('v2', 'figure'),
    Output('v3', 'figure'),
    Output('v4', 'figure'),
    Output('v5', 'figure'),
    Output('data-count', 'children'),
    Output('year-label',  'children'),
    Input('genre-filter', 'value'),
    Input('year-filter',  'value'),
    Input('theme-store',  'data'),
)
def update_all(genres, year_range, theme):
    filtered = df[
        df['playlist_genre'].isin(genres) &
        df['year'].between(year_range[0], year_range[1])
    ]
    count      = f'{len(filtered):,} titres'
    year_label = f'Période : {year_range[0]} – {year_range[1]}'

    # Pass theme so each component can style its figure accordingly
    figs = [v1(filtered, theme), v2(filtered, theme),
            v3(filtered, theme), v4(filtered, theme), v5(filtered, theme)]
    return *figs, count, year_label


# ── Callback: fullscreen ──────────────────────────────────────────────────────
BASE_CLASSES = ['viz-card'] * 5

@app.callback(
    Output('card-v1', 'className'),
    Output('card-v2', 'className'),
    Output('card-v3', 'className'),
    Output('card-v4', 'className'),
    Output('card-v5', 'className'),
    Output('close-fullscreen', 'style'),
    Input('fullscreen-v1', 'n_clicks'),
    Input('fullscreen-v2', 'n_clicks'),
    Input('fullscreen-v3', 'n_clicks'),
    Input('fullscreen-v4', 'n_clicks'),
    Input('fullscreen-v5', 'n_clicks'),
    Input('close-fullscreen', 'n_clicks'),
    prevent_initial_call=True,
)
def toggle_fullscreen(n1, n2, n3, n4, n5, n_close):
    triggered    = dash.ctx.triggered_id
    classes      = list(BASE_CLASSES)
    close_style  = {'display': 'none'}
    if triggered != 'close-fullscreen':
        idx = int(triggered.split('-v')[1]) - 1
        classes[idx] += ' viz-fullscreen'
        close_style = {'display': 'flex'}
    return *classes, close_style


if __name__ == '__main__':
    app.run(debug=True)
