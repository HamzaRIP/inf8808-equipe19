import dash
from dash import dcc, html, Input, Output
import pandas as pd

from components.v1_bar_chart import render as v1
from components.v2_dumbbell import render as v2
from components.v3_bubble import render as v3_render
from components.v3_bubble import V3_SIZE_OPTIONS, V3_X_OPTIONS, V3_Y_OPTIONS
from components.v4_chord import render as v4
from components.v5_slope import render as v5

# ── Load data ────────────────────────────────────────────────────────────────
df = pd.read_csv('spotify_songs.csv')
df['year'] = pd.to_datetime(df['track_album_release_date'], errors='coerce').dt.year
df = df.dropna(subset=['year', 'track_popularity'])
df['year'] = df['year'].astype(int)

GENRES = sorted(df['playlist_genre'].dropna().unique().tolist())
MIN_YEAR = int(df['year'].min())
MAX_YEAR = int(df['year'].max())

V3_TOP_N_MAX = 80

# ── App ──────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__)
server = app.server          # ← add this line
app.title = 'Spotify Factors — Équipe 19'

app.layout = html.Div(className='dashboard', children=[

    # ── Header ───────────────────────────────────────────────────────────────
    html.Header(className='header', children=[
        html.Div(className='header-left', children=[
            html.Span('♫', className='logo'),
            html.Div([
                html.H1('Spotify Factors'),
                html.P('INF8808 · Équipe 19'),
            ])
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
                    className='year-slider',
                ),
            ]),
            html.Div(id='data-count', className='data-count'),
        ]),
    ]),

    # ── Grid ─────────────────────────────────────────────────────────────────
    html.Main(className='grid', children=[
        html.Div(className='viz-card', children=[
            html.Div(className='viz-label', children=[
                '01 — BAR CHART CORRÉLATIONS',
                html.Span('Q1 · Q4 · Q5'),
            ]),
            dcc.Graph(id='v1', className='viz-graph', config={'displayModeBar': False}),
        ]),
        html.Div(className='viz-card', children=[
            html.Div(className='viz-label', children=[
                '02 — DUMBBELL CHART',
                html.Span('Q2 · Q3'),
            ]),
            dcc.Graph(id='v2', className='viz-graph', config={'displayModeBar': False}),
        ]),
        html.Div(className='viz-card viz-card-v3', children=[
            html.Div(className='viz-label', children=[
                '03 — BUBBLE CHART',
                html.Span('Q5 · Q7 · Q8'),
            ]),
            html.Div(className='viz-v3-body', children=[
                dcc.Graph(id='v3', className='viz-graph viz-graph-v3', config={'displayModeBar': False}),
                html.Div(className='viz-v3-params', children=[
                    html.Div('Paramètres', className='viz-v3-params-title'),
                    html.Label('Axe X', className='viz-v3-field-label'),
                    dcc.Dropdown(
                        id='v3-axis-x',
                        options=V3_X_OPTIONS,
                        value='acousticness_sqrt',
                        clearable=False,
                        className='viz-v3-dropdown',
                    ),
                    html.Label('Axe Y', className='viz-v3-field-label'),
                    dcc.Dropdown(
                        id='v3-axis-y',
                        options=V3_Y_OPTIONS,
                        value='track_popularity',
                        clearable=False,
                        className='viz-v3-dropdown',
                    ),
                    html.Label('Taille', className='viz-v3-field-label'),
                    dcc.Dropdown(
                        id='v3-size',
                        options=V3_SIZE_OPTIONS,
                        value='valence',
                        clearable=False,
                        className='viz-v3-dropdown',
                    ),
                    html.Label('Top N', className='viz-v3-field-label'),
                    dcc.Slider(
                        id='v3-top-n',
                        min=3,
                        max=V3_TOP_N_MAX,
                        step=1,
                        value=18,
                        marks=None,
                        tooltip={'placement': 'bottom', 'always_visible': False},
                        className='viz-v3-slider',
                    ),
                ]),
            ]),
        ]),
        html.Div(className='viz-card viz-wide', children=[
            html.Div(className='viz-label', children=[
                '04 — CHORD DIAGRAM',
                html.Span('Q6 · Q9 · Q10'),
            ]),
            dcc.Graph(id='v4', className='viz-graph', config={'displayModeBar': False}),
        ]),
        html.Div(className='viz-card viz-wide', children=[
            html.Div(className='viz-label', children=[
                '05 — SLOPE CHART TEMPOREL',
                html.Span('Q10–13'),
            ]),
            dcc.Graph(id='v5', className='viz-graph', config={'displayModeBar': False}),
        ]),
    ]),
])

# ── Callbacks ────────────────────────────────────────────────────────────────
@app.callback(
    Output('v1', 'figure'),
    Output('v2', 'figure'),
    Output('v4', 'figure'),
    Output('v5', 'figure'),
    Output('data-count', 'children'),
    Output('year-label', 'children'),
    Input('genre-filter', 'value'),
    Input('year-filter', 'value'),
)
def update_all(genres, year_range):
    if not genres:
        filtered = df.iloc[0:0]
    else:
        filtered = df[
            df['playlist_genre'].isin(genres) &
            df['year'].between(year_range[0], year_range[1])
        ]
    count = f'{len(filtered):,} titres'
    year_label = f'Période : {year_range[0]} – {year_range[1]}'
    return v1(filtered), v2(filtered), v4(filtered), v5(filtered), count, year_label


@app.callback(
    Output('v3', 'figure'),
    Input('genre-filter', 'value'),
    Input('year-filter', 'value'),
    Input('v3-axis-x', 'value'),
    Input('v3-axis-y', 'value'),
    Input('v3-size', 'value'),
    Input('v3-top-n', 'value'),
)
def update_v3(genres, year_range, x_key, y_key, size_key, top_n):
    if not genres:
        filtered = df.iloc[0:0]
    else:
        filtered = df[
            df['playlist_genre'].isin(genres) &
            df['year'].between(year_range[0], year_range[1])
        ]
    x_key = x_key or 'acousticness_sqrt'
    y_key = y_key or 'track_popularity'
    size_key = size_key or 'valence'
    n = int(top_n) if top_n is not None else 18
    n = max(1, min(n, V3_TOP_N_MAX))
    return v3_render(filtered, x_key, y_key, size_key, n)


if __name__ == '__main__':
    app.run(debug=True)
