"""
Visualisation 01 — Bar chart des corrélations avec la popularité.
(contenu précédemment dans v2_dumbbell.py)
"""
import plotly.graph_objects as go
import pandas as pd
import numpy as np

THEME = {
    'dark': {
        'bg': '#0a0a0f', 'grid': 'rgba(255,255,255,0.08)',
        'text': '#c8c8d8', 'muted': '#6b6b82',
        'zeroline': 'rgba(255,255,255,0.35)',
    },
    'light': {
        'bg': '#f5f5f0', 'grid': 'rgba(0,0,0,0.08)',
        'text': '#1a1a1a', 'muted': '#888880',
        'zeroline': 'rgba(0,0,0,0.35)',
    },
}

POSITIVE_CLR = '#1db954'   # vert Spotify
NEGATIVE_CLR = '#A0A0A0'   # gris
FONT_MONO = 'Space Mono, monospace'

FEATURE_ORDER = [
    'acousticness', 'danceability', 'loudness', 'valence',
    'mode', 'speechiness', 'key', 'tempo',
    'liveness', 'energy', 'duration_ms', 'instrumentalness',
]
FEATURE_LABELS = {
    'acousticness': 'Acousticness', 'danceability': 'Danceability',
    'duration_ms': 'Duration', 'energy': 'Energy',
    'instrumentalness': 'Instrumentalness', 'key': 'Key',
    'liveness': 'Liveness', 'loudness': 'Loudness', 'mode': 'Mode',
    'speechiness': 'Speechiness', 'tempo': 'Tempo', 'valence': 'Valence',
}
TARGET = 'track_popularity'


def _empty_fig(msg='Données insuffisantes', t=None):
    t = t or THEME['dark']
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor=t['bg'], paper_bgcolor=t['bg'], font_color=t['muted'],
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        annotations=[dict(text=msg, x=0.5, y=0.5, xref='paper', yref='paper',
                          showarrow=False, font=dict(size=14, color=t['muted'], family=FONT_MONO))],
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


def render(df: pd.DataFrame, theme: str = 'dark') -> go.Figure:
    t = THEME.get(theme, THEME['dark'])
    if df.empty or TARGET not in df.columns:
        return _empty_fig(t=t)

    cols = [c for c in FEATURE_ORDER if c in df.columns]
    rows = []
    for col in cols:
        subset = df[[col, TARGET]].dropna()
        if len(subset) < 3 or subset[col].nunique() <= 1 or subset[TARGET].nunique() <= 1:
            continue
        rows.append({'feature': col, 'label': FEATURE_LABELS.get(col, col),
                     'corr': subset[col].corr(subset[TARGET])})
    if not rows:
        return _empty_fig('Impossible de calculer les corrélations.', t=t)

    corr_df = pd.DataFrame(rows)
    corr_df['feature'] = pd.Categorical(
        corr_df['feature'],
        categories=[c for c in FEATURE_ORDER if c in corr_df['feature'].values],
        ordered=True)
    corr_df = corr_df.sort_values('corr', ascending=True)

    colors = [POSITIVE_CLR if v >= 0 else NEGATIVE_CLR for v in corr_df['corr']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=corr_df['corr'],
        y=corr_df['label'],
        orientation='h',
        marker=dict(color=colors, line=dict(color='rgba(0,0,0,0)', width=0)),
        hovertemplate='<b>%{y}</b><br>Corrélation avec la popularité : %{x:.3f}<extra></extra>',
    ))
    fig.update_layout(
        plot_bgcolor=t['bg'], paper_bgcolor=t['bg'],
        font=dict(color=t['text'], family=FONT_MONO, size=11),
        bargap=0.25,
        title=dict(
            text='Corrélations des attributs audio avec la popularité',
            x=0.02, xanchor='left',
            font=dict(size=13, color=t['text'], family=FONT_MONO),
        ),
        xaxis=dict(
            title='Coefficient de corrélation de Pearson', range=[-0.5, 0.5],
            showgrid=True, gridcolor=t['grid'],
            zeroline=True, zerolinecolor=t['zeroline'], zerolinewidth=2,
            tickvals=[-0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4],
            tickfont=dict(color=t['text']), fixedrange=True,
        ),
        yaxis=dict(
            title='', showgrid=False, fixedrange=True,
            tickfont=dict(color=t['text']),
        ),
        autosize=True,
        margin=dict(l=120, r=20, t=50, b=40),
        dragmode=False, hovermode='closest',
    )
    return fig
