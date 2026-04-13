"""
Visualisation 03 — nuage de bulles par sous-genre (circle packing + Plotly).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

THEME = {
    'dark': {
        'bg': '#0a0a0f', 'grid': 'rgba(255,255,255,0.06)',
        'text': '#c8c8d8', 'muted': '#6b6b82',
        'hover_bg': '#1a1a24',
    },
    'light': {
        'bg': '#f5f5f0', 'grid': 'rgba(0,0,0,0.07)',
        'text': '#1a1a1a', 'muted': '#888880',
        'hover_bg': '#e0e0d8',
    },
}

FONT_MONO = 'Space Mono, monospace'

COLORS_GENRE = {
    'pop':   '#1DB954', 
    'rap':   '#F4A261',
    'rock':  '#E63946', 
    'latin': '#A8DADC',
    'r&b':   '#C77DFF', 
    'edm':   '#00B4D8',
}
FALLBACK_GENRE_COLOR = '#6d6d78'

_PACK_ITERS = 200
_SCALE_BISECT_STEPS = 10
_SCALE_LO, _SCALE_HI = 4.0, 82.0
_DIAM_VISUAL_SCALE = 0.48
_MARKER_DIAM_MIN, _MARKER_DIAM_MAX = 4.0, 44.0

_NUM_COLS = (
    'track_popularity', 'danceability', 'energy', 'speechiness',
    'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo',
)
_LABELS = {
    'track_popularity': 'Popularité', 'danceability': 'Danceability',
    'energy': 'Énergie', 'speechiness': 'Speechiness',
    'acousticness': 'Acousticness', 'acousticness_sqrt': 'Acousticness (racine)',
    'instrumentalness': 'Instrumentalness', 'liveness': 'Liveness',
    'valence': 'Valence', 'tempo': 'Tempo', 'effectif': 'Effectif (titres)',
}

V3_X_OPTIONS = [
    {'label': 'Acousticness (racine)', 'value': 'acousticness_sqrt'},
    {'label': 'Acousticness',          'value': 'acousticness'},
    {'label': 'Énergie',               'value': 'energy'},
    {'label': 'Danceability',          'value': 'danceability'},
    {'label': 'Valence',               'value': 'valence'},
    {'label': 'Speechiness',           'value': 'speechiness'},
    {'label': 'Instrumentalness',      'value': 'instrumentalness'},
    {'label': 'Liveness',              'value': 'liveness'},
    {'label': 'Tempo',                 'value': 'tempo'},
]
V3_Y_OPTIONS = [
    {'label': 'Popularité',   'value': 'track_popularity'},
    {'label': 'Énergie',      'value': 'energy'},
    {'label': 'Danceability', 'value': 'danceability'},
    {'label': 'Valence',      'value': 'valence'},
    {'label': 'Acousticness', 'value': 'acousticness'},
    {'label': 'Speechiness',  'value': 'speechiness'},
    {'label': 'Liveness',     'value': 'liveness'},
    {'label': 'Tempo',        'value': 'tempo'},
]
V3_SIZE_OPTIONS = [
    {'label': 'Valence',      'value': 'valence'},
    {'label': 'Effectif',     'value': 'effectif'},
    {'label': 'Énergie',      'value': 'energy'},
    {'label': 'Danceability', 'value': 'danceability'},
]


def _empty_fig(msg: str = 'Données insuffisantes', t=None) -> go.Figure:
    t = t or THEME['dark']
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor=t['bg'], paper_bgcolor=t['bg'], font_color=t['muted'],
        font_family=FONT_MONO,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        annotations=[dict(text=msg, x=0.5, y=0.5, xref='paper', yref='paper',
                          showarrow=False, font=dict(size=12, color=t['muted'], family=FONT_MONO))],
        margin=dict(l=8, r=8, t=28, b=8),
    )
    return fig


def _pack_bubbles_v2(x, y, radii, bounds_px, iterations=_PACK_ITERS,
                     attraction=0.004, padding=0.0):
    cx = x.astype(float).copy(); cy = y.astype(float).copy()
    ox = x.astype(float).copy(); oy = y.astype(float).copy()
    n = len(cx); xlo, xhi, ylo, yhi = bounds_px
    for it in range(iterations):
        att = attraction * (0.5 + 1.5 * it / max(iterations, 1))
        for i in range(n):
            for j in range(i + 1, n):
                dx = cx[i] - cx[j]; dy = cy[i] - cy[j]
                dist = float(np.sqrt(dx*dx + dy*dy)) + 1e-6
                min_dist = radii[i] + radii[j] + padding
                if dist < min_dist:
                    overlap = (min_dist - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    cx[i] += overlap * ux; cx[j] -= overlap * ux
                    cy[i] += overlap * uy; cy[j] -= overlap * uy
        for i in range(n):
            cx[i] = np.clip(cx[i], xlo + radii[i], xhi - radii[i])
            cy[i] = np.clip(cy[i], ylo + radii[i], yhi - radii[i])
        cx += (ox - cx) * att; cy += (oy - cy) * att
    return cx, cy


def _find_max_scale(x_px, y_px, rel_radii, bounds_px, iterations=_PACK_ITERS,
                    attraction=0.004, tol=50.0):
    lo, hi = _SCALE_LO, _SCALE_HI
    best_scale = lo; best_cx, best_cy = x_px.copy(), y_px.copy()
    for _ in range(_SCALE_BISECT_STEPS):
        mid = (lo + hi) / 2; radii = rel_radii * mid
        cx, cy = _pack_bubbles_v2(x_px, y_px, radii, bounds_px,
                                   iterations=iterations, attraction=attraction)
        xlo, xhi, ylo, yhi = bounds_px
        in_bounds = all(
            cx[i]-radii[i] >= xlo-tol and cx[i]+radii[i] <= xhi+tol and
            cy[i]-radii[i] >= ylo-tol and cy[i]+radii[i] <= yhi+tol
            for i in range(len(cx)))
        max_overlap = 0.0
        for i in range(len(cx)):
            for j in range(i+1, len(cx)):
                dist = float(np.sqrt((cx[i]-cx[j])**2 + (cy[i]-cy[j])**2))
                overlap = radii[i] + radii[j] - dist
                if overlap > max_overlap: max_overlap = overlap
        if in_bounds and max_overlap < 3:
            best_scale = mid; best_cx, best_cy = cx.copy(), cy.copy(); lo = mid
        else:
            hi = mid
    return best_scale, best_cx, best_cy


def _aggregate_subgenres(df: pd.DataFrame) -> pd.DataFrame:
    need = {'playlist_subgenre', 'playlist_genre', *_NUM_COLS}
    if need - set(df.columns):
        return pd.DataFrame()
    work = df.dropna(subset=['playlist_subgenre', 'playlist_genre']).copy()
    if work.empty:
        return pd.DataFrame()
    mean_cols = [c for c in _NUM_COLS if c in work.columns]
    if not mean_cols:
        return pd.DataFrame()
    agg_dict = {c: 'mean' for c in mean_cols}
    id_col = 'track_id' if 'track_id' in work.columns else work.columns[0]
    agg_dict[id_col] = 'count'
    g = work.groupby(['playlist_subgenre', 'playlist_genre'], as_index=False).agg(agg_dict)
    return g.rename(columns={id_col: 'effectif'})


def render(df: pd.DataFrame, x_key: str, y_key: str,
           size_key: str, top_n: int, theme: str = 'dark') -> go.Figure:
    t = THEME.get(theme, THEME['dark'])
    if df is None or df.empty:
        return _empty_fig(t=t)

    sub = _aggregate_subgenres(df)
    if sub.empty:
        return _empty_fig('Pas de sous-genres dans la sélection', t=t)

    if x_key != 'acousticness_sqrt' and x_key not in sub.columns:
        return _empty_fig('Axe X invalide', t=t)
    if y_key not in sub.columns:
        return _empty_fig('Axe Y invalide', t=t)
    if size_key not in sub.columns:
        return _empty_fig('Taille invalide', t=t)

    sub = sub.sort_values('track_popularity', ascending=False)
    sub = sub.head(max(1, min(int(top_n), len(sub)))).reset_index(drop=True)

    need = [y_key, 'acousticness'] if x_key == 'acousticness_sqrt' else [y_key]
    if x_key != 'acousticness_sqrt' and x_key in sub.columns:
        need.append(x_key)
    if size_key in sub.columns and size_key != 'effectif':
        need.append(size_key)
    sub = sub.dropna(subset=[c for c in need if c in sub.columns])
    if sub.empty:
        return _empty_fig('Valeurs manquantes pour les axes choisis', t=t)

    n = len(sub)
    x_data = (np.sqrt(np.clip(sub['acousticness'].to_numpy(dtype=float), 0, 1))
               if x_key == 'acousticness_sqrt' else sub[x_key].to_numpy(dtype=float))
    y_data = sub[y_key].to_numpy(dtype=float)
    sizes_raw = (sub['effectif'].to_numpy(dtype=float)
                 if size_key == 'effectif' else sub[size_key].to_numpy(dtype=float))

    x_min, x_max = float(np.min(x_data)), float(np.max(x_data))
    y_min, y_max = float(np.min(y_data)), float(np.max(y_data))
    x_margin = (x_max - x_min) * 0.15 + 1e-6; y_margin = (y_max - y_min) * 0.15 + 1e-6
    x_min -= x_margin; x_max += x_margin; y_min -= y_margin; y_max += y_margin

    smin, smax = float(np.min(sizes_raw)), float(np.max(sizes_raw))
    rel_radii = (np.ones(n, dtype=float) * 0.7 if smax <= smin
                 else 0.4 + 0.6 * (sizes_raw - smin) / (smax - smin))

    W = H = 500.0; bounds_px = (0.0, W, 0.0, H)
    dx, dy = x_max - x_min, y_max - y_min
    x_px = np.full(n, W / 2.0) if dx < 1e-12 else (x_data - x_min) / dx * W
    y_px = np.full(n, H / 2.0) if dy < 1e-12 else (y_data - y_min) / dy * H

    if n == 1:
        best_scale = 42.0; packed_x_px = x_px.copy(); packed_y_px = y_px.copy()
    else:
        best_scale, packed_x_px, packed_y_px = _find_max_scale(
            x_px, y_px, rel_radii, bounds_px)

    final_radii_px = rel_radii * best_scale
    diameters = np.clip(2 * final_radii_px * _DIAM_VISUAL_SCALE,
                        _MARKER_DIAM_MIN, _MARKER_DIAM_MAX)

    px = np.clip(packed_x_px, 0.0, W); py = np.clip(packed_y_px, 0.0, H)
    x_packed = np.full(n, (x_min + x_max) / 2) if dx < 1e-12 else x_min + (px / W) * dx
    y_packed = np.full(n, (y_min + y_max) / 2) if dy < 1e-12 else y_min + (py / H) * dy

    genres = sub['playlist_genre'].astype(str).str.lower().to_numpy()
    labels = sub['playlist_subgenre'].astype(str).to_numpy()
    x_for_hover = x_data
    mean_pop = sub['track_popularity'].to_numpy(dtype=float)
    effectif = sub['effectif'].to_numpy(dtype=float)
    x_label = _LABELS.get(x_key, x_key)
    y_label = _LABELS.get(y_key, y_key)

    fig = go.Figure()
    for g in np.unique(genres):
        mask = genres == g
        color = COLORS_GENRE.get(g, FALLBACK_GENRE_COLOR)
        fig.add_trace(go.Scattergl(
            x=x_packed[mask], y=y_packed[mask], mode='markers',
            name=g.upper(), legendgroup=g,
            marker=dict(size=diameters[mask], sizemode='diameter', color=color,
                        opacity=0.9, line=dict(color='rgba(255,255,255,0.28)', width=0.6)),
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>'
                + f'{y_label}: %{{customdata[1]:.2f}}<br>'
                + f'{x_label}: %{{customdata[2]:.4f}}<br>'
                + 'Effectif: %{customdata[3]}<extra></extra>'),
            customdata=np.stack([labels[mask], mean_pop[mask],
                                  x_for_hover[mask], effectif[mask]], axis=-1),
        ))

    fig.update_layout(
        paper_bgcolor=t['bg'], plot_bgcolor=t['bg'],
        font=dict(color=t['text'], family=FONT_MONO),
        title=dict(text='Q5, Q7, Q8 — Popularité et signature audio par sous-genre',
                   font=dict(size=11, color=t['text']), x=0.5, xanchor='center'),
        margin=dict(l=44, r=8, t=40, b=56),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.22, x=0,
                    font=dict(size=9, color=t['text']), bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(title=dict(text=x_label, font=dict(color=t['text'], size=11)),
                   range=[x_min, x_max], gridcolor=t['grid'], zeroline=False,
                   tickfont=dict(size=9, color=t['text']),
                   linecolor='rgba(128,128,128,0.2)', mirror=False),
        yaxis=dict(title=dict(text=y_label, font=dict(color=t['text'], size=11)),
                   range=[y_min, y_max], gridcolor=t['grid'], zeroline=False,
                   tickfont=dict(size=9, color=t['text']),
                   linecolor='rgba(128,128,128,0.2)', mirror=False),
        hoverlabel=dict(bgcolor=t['hover_bg'], font_size=11, font_family=FONT_MONO),
        hovermode='closest',
    )
    return fig
