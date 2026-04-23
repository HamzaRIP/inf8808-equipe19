"""
Visualisation 02 — Dumbbell chart.
Compare la valeur moyenne de chaque attribut audio entre les titres
populaires (quartile supérieur) et impopulaires (quartile inférieur).
Chaque feature est normalisée sur [0,1] pour permettre la comparaison.
"""
import plotly.graph_objects as go
import pandas as pd
import numpy as np

THEME = {
    'dark': {
        'bg': '#0a0a0f', 'grid': 'rgba(255,255,255,0.07)',
        'text': '#c8c8d8', 'muted': '#6b6b82',
        'bar_bg': 'rgba(255,255,255,0.04)',
        'hover_bg': '#1a1a24',
    },
    'light': {
        'bg': '#f5f5f0', 'grid': 'rgba(0,0,0,0.08)',
        'text': '#1a1a1a', 'muted': '#888880',
        'bar_bg': 'rgba(0,0,0,0.04)',
        'hover_bg': '#e0e0d8',
    },
}

# Couleurs des deux groupes
POP_CLR   = '#1db954'   # vert Spotify  — populaire
UNPOP_CLR = '#6b6b82'   # gris muted    — impopulaire
FONT_MONO = 'Space Mono, monospace'

TARGET = 'track_popularity'

# Features affichées et leur ordre d'affichage (du bas vers le haut dans le graphe)
FEATURES = [
    ('instrumentalness', 'Instrumentalness'),
    ('liveness',         'Liveness'),
    ('speechiness',      'Speechiness'),
    ('acousticness',     'Acousticness'),
    ('tempo',            'Tempo'),
    ('loudness',         'Loudness'),
    ('valence',          'Valence'),
    ('energy',           'Énergie'),
    ('danceability',     'Danceability'),
]


def _normalize_series(s: pd.Series) -> pd.Series:
    """Min-max normalisation sur [0, 1]."""
    mn, mx = s.min(), s.max()
    if mx - mn < 1e-9:
        return pd.Series([0.5] * len(s), index=s.index)
    return (s - mn) / (mx - mn)


def _empty_fig(msg='Données insuffisantes', t=None):
    t = t or THEME['dark']
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor=t['bg'], paper_bgcolor=t['bg'], font_color=t['muted'],
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        annotations=[dict(text=msg, x=0.5, y=0.5, xref='paper', yref='paper',
                          showarrow=False,
                          font=dict(size=14, color=t['muted'], family=FONT_MONO))],
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


def render(df: pd.DataFrame, theme: str = 'dark') -> go.Figure:
    t = THEME.get(theme, THEME['dark'])

    if df.empty or TARGET not in df.columns:
        return _empty_fig(t=t)

    # Seuils popularité
    q25 = df[TARGET].quantile(0.25)
    q75 = df[TARGET].quantile(0.75)

    pop_df   = df[df[TARGET] >= q75].copy()
    unpop_df = df[df[TARGET] <= q25].copy()

    if len(pop_df) < 5 or len(unpop_df) < 5:
        return _empty_fig('Pas assez de données pour les deux groupes.', t=t)

    # Construire les données par feature
    labels_list, pop_vals, unpop_vals = [], [], []

    for col, label in FEATURES:
        if col not in df.columns:
            continue
        # Normalisation globale (sur tout le df) pour comparaison cohérente
        norm = _normalize_series(df[col])
        idx_pop   = pop_df.index.intersection(norm.index)
        idx_unpop = unpop_df.index.intersection(norm.index)
        if len(idx_pop) < 2 or len(idx_unpop) < 2:
            continue
        labels_list.append(label)
        pop_vals.append(float(norm.loc[idx_pop].mean()))
        unpop_vals.append(float(norm.loc[idx_unpop].mean()))

    if not labels_list:
        return _empty_fig(t=t)

    n = len(labels_list)
    y_pos = list(range(n))   # positions verticales

    fig = go.Figure()

    # ── Segments reliant les deux points (le "bâton" du dumbbell) ──
    for i in range(n):
        x_lo = min(pop_vals[i], unpop_vals[i])
        x_hi = max(pop_vals[i], unpop_vals[i])
        fig.add_shape(
            type='line',
            x0=x_lo, x1=x_hi, y0=i, y1=i,
            line=dict(color=t['grid'], width=2),
        )

    # ── Groupe impopulaire (point gauche en général) ──
    fig.add_trace(go.Scatter(
        x=unpop_vals, y=y_pos,
        mode='markers',
        name=f'Impopulaires (≤ Q25 = {int(q25)})',
        marker=dict(
            color=UNPOP_CLR, size=14,
            line=dict(color=t['bg'], width=2),
            symbol='circle',
        ),
        hovertemplate=(
            '<b>%{customdata}</b><br>'
            'Impopulaires : %{x:.3f}<extra></extra>'
        ),
        customdata=labels_list,
    ))

    # ── Groupe populaire (point vert) ──
    fig.add_trace(go.Scatter(
        x=pop_vals, y=y_pos,
        mode='markers',
        name=f'Populaires (≥ Q75 = {int(q75)})',
        marker=dict(
            color=POP_CLR, size=14,
            line=dict(color=t['bg'], width=2),
            symbol='circle',
        ),
        hovertemplate=(
            '<b>%{customdata}</b><br>'
            'Populaires : %{x:.3f}<extra></extra>'
        ),
        customdata=labels_list,
    ))

    # ── Annotations de différence ──
    annotations = []
    for i in range(n):
        diff = pop_vals[i] - unpop_vals[i]
        sign = '+' if diff >= 0 else ''
        color_diff = POP_CLR if diff > 0.005 else (UNPOP_CLR if diff < -0.005 else t['muted'])
        annotations.append(dict(
            x=1.02, y=i,
            xref='paper', yref='y',
            text=f'{sign}{diff:.2f}',
            showarrow=False,
            font=dict(color=color_diff, family=FONT_MONO, size=10),
            xanchor='left', yanchor='middle',
        ))

    fig.update_layout(
        plot_bgcolor=t['bg'],
        paper_bgcolor=t['bg'],
        font=dict(color=t['text'], family=FONT_MONO, size=11),

        title=dict(
            text='Profil audio : titres populaires vs impopulaires',
            x=0.02, xanchor='left',
            font=dict(size=13, color=t['text'], family=FONT_MONO),
        ),

        xaxis=dict(
            title='Valeur normalisée (0 – 1)',
            range=[-0.05, 1.05],
            showgrid=True, gridcolor=t['grid'],
            zeroline=False,
            tickvals=[0, 0.25, 0.5, 0.75, 1.0],
            ticktext=['0', '0.25', '0.5', '0.75', '1'],
            tickfont=dict(color=t['text']),
            fixedrange=True,
        ),
        yaxis=dict(
            tickvals=y_pos,
            ticktext=labels_list,
            tickfont=dict(color=t['text'], size=11),
            showgrid=True, gridcolor=t['bar_bg'],
            zeroline=False,
            range=[-0.7, n - 0.3],
            fixedrange=True,
        ),

        legend=dict(
            orientation='h',
            x=0.02, y=1.04,
            xanchor='left', yanchor='bottom',
            font=dict(size=10, family=FONT_MONO, color=t['text']),
            bgcolor='rgba(0,0,0,0)',
        ),

        annotations=annotations,
        margin=dict(l=130, r=80, t=60, b=50),
        dragmode=False,
        hovermode='closest',
        hoverlabel=dict(bgcolor=t['hover_bg'], font_size=11, font_family=FONT_MONO),
    )

    return fig
