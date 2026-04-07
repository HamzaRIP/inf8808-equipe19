"""
Visualisation 03 — nuage de bulles par sous-genre (circle packing + Plotly).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ── Thème (aligné v5) ─────────────────────────────────────────────────────────
BG = "#0a0a0f"
GRID_CLR = "rgba(255,255,255,0.06)"
TEXT_CLR = "#c8c8d8"
TEXT_MUTED = "#6b6b82"
FONT_MONO = "Space Mono, monospace"

# Palette genre parent (légèrement assombrie pour lisibilité du texte clair)
COLORS_GENRE = {
    "pop": "#E74C3C",
    "rock": "#6d6d78",
    "r&b": "#A569BD",
    "rap": "#2C3E50",
    "latin": "#C9780E",
    "edm": "#4A90C2",
}
FALLBACK_GENRE_COLOR = "#6d6d78"

# Perf packing (moins d’itérations) + bulles plus petites visuellement
_PACK_ITERS = 200
_SCALE_BISECT_STEPS = 10
_SCALE_LO, _SCALE_HI = 4.0, 82.0
_DIAM_VISUAL_SCALE = 0.48
_MARKER_DIAM_MIN, _MARKER_DIAM_MAX = 4.0, 44.0

# Colonnes numériques agrégées (moyennes)
_NUM_COLS = (
    "track_popularity",
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
)

_LABELS = {
    "track_popularity": "Popularité",
    "danceability": "Danceability",
    "energy": "Énergie",
    "speechiness": "Speechiness",
    "acousticness": "Acousticness",
    "acousticness_sqrt": "Acousticness (racine)",
    "instrumentalness": "Instrumentalness",
    "liveness": "Liveness",
    "valence": "Valence",
    "tempo": "Tempo",
    "effectif": "Effectif (titres)",
}

# Options Dash (value -> clé interne)
V3_X_OPTIONS = [
    {"label": "Acousticness (racine)", "value": "acousticness_sqrt"},
    {"label": "Acousticness", "value": "acousticness"},
    {"label": "Énergie", "value": "energy"},
    {"label": "Danceability", "value": "danceability"},
    {"label": "Valence", "value": "valence"},
    {"label": "Speechiness", "value": "speechiness"},
    {"label": "Instrumentalness", "value": "instrumentalness"},
    {"label": "Liveness", "value": "liveness"},
    {"label": "Tempo", "value": "tempo"},
]

V3_Y_OPTIONS = [
    {"label": "Popularité", "value": "track_popularity"},
    {"label": "Énergie", "value": "energy"},
    {"label": "Danceability", "value": "danceability"},
    {"label": "Valence", "value": "valence"},
    {"label": "Acousticness", "value": "acousticness"},
    {"label": "Speechiness", "value": "speechiness"},
    {"label": "Liveness", "value": "liveness"},
    {"label": "Tempo", "value": "tempo"},
]

V3_SIZE_OPTIONS = [
    {"label": "Valence", "value": "valence"},
    {"label": "Effectif", "value": "effectif"},
    {"label": "Énergie", "value": "energy"},
    {"label": "Danceability", "value": "danceability"},
]


def _empty_fig(msg: str = "Données insuffisantes") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        font_color=TEXT_MUTED,
        font_family=FONT_MONO,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text=msg,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=12, color=TEXT_MUTED, family=FONT_MONO),
            )
        ],
        margin=dict(l=8, r=8, t=28, b=8),
    )
    return fig


def _pack_bubbles_v2(
    x: np.ndarray,
    y: np.ndarray,
    radii: np.ndarray,
    bounds_px: tuple[float, float, float, float],
    iterations: int = _PACK_ITERS,
    attraction: float = 0.004,
    padding: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    cx = x.astype(float).copy()
    cy = y.astype(float).copy()
    ox, oy = x.astype(float).copy(), y.astype(float).copy()
    n = len(cx)
    xlo, xhi, ylo, yhi = bounds_px

    for it in range(iterations):
        att = attraction * (0.5 + 1.5 * it / max(iterations, 1))

        for i in range(n):
            for j in range(i + 1, n):
                dx = cx[i] - cx[j]
                dy = cy[i] - cy[j]
                dist = float(np.sqrt(dx * dx + dy * dy)) + 1e-6
                min_dist = radii[i] + radii[j] + padding
                if dist < min_dist:
                    overlap = (min_dist - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    cx[i] += overlap * ux
                    cx[j] -= overlap * ux
                    cy[i] += overlap * uy
                    cy[j] -= overlap * uy

        for i in range(n):
            cx[i] = np.clip(cx[i], xlo + radii[i], xhi - radii[i])
            cy[i] = np.clip(cy[i], ylo + radii[i], yhi - radii[i])

        cx += (ox - cx) * att
        cy += (oy - cy) * att

    return cx, cy


def _find_max_scale(
    x_px: np.ndarray,
    y_px: np.ndarray,
    rel_radii: np.ndarray,
    bounds_px: tuple[float, float, float, float],
    iterations: int = _PACK_ITERS,
    attraction: float = 0.004,
    tol: float = 50.0,
) -> tuple[float, np.ndarray, np.ndarray]:
    lo, hi = _SCALE_LO, _SCALE_HI
    best_scale = lo
    best_cx, best_cy = x_px.copy(), y_px.copy()

    for _ in range(_SCALE_BISECT_STEPS):
        mid = (lo + hi) / 2
        radii = rel_radii * mid
        cx, cy = _pack_bubbles_v2(
            x_px, y_px, radii, bounds_px, iterations=iterations, attraction=attraction
        )

        xlo, xhi, ylo, yhi = bounds_px
        in_bounds = all(
            cx[i] - radii[i] >= xlo - tol
            and cx[i] + radii[i] <= xhi + tol
            and cy[i] - radii[i] >= ylo - tol
            and cy[i] + radii[i] <= yhi + tol
            for i in range(len(cx))
        )

        max_overlap = 0.0
        for i in range(len(cx)):
            for j in range(i + 1, len(cx)):
                dist = float(
                    np.sqrt((cx[i] - cx[j]) ** 2 + (cy[i] - cy[j]) ** 2)
                )
                overlap = radii[i] + radii[j] - dist
                if overlap > max_overlap:
                    max_overlap = overlap

        if in_bounds and max_overlap < 3:
            best_scale = mid
            best_cx, best_cy = cx.copy(), cy.copy()
            lo = mid
        else:
            hi = mid

    return best_scale, best_cx, best_cy


def _aggregate_subgenres(df: pd.DataFrame) -> pd.DataFrame:
    need = {"playlist_subgenre", "playlist_genre", *_NUM_COLS}
    missing = need - set(df.columns)
    if missing:
        return pd.DataFrame()

    work = df.dropna(subset=["playlist_subgenre", "playlist_genre"]).copy()
    if work.empty:
        return pd.DataFrame()

    mean_cols = [c for c in _NUM_COLS if c in work.columns]
    if not mean_cols:
        return pd.DataFrame()
    agg_dict = {c: "mean" for c in mean_cols}
    id_col = "track_id" if "track_id" in work.columns else work.columns[0]
    agg_dict[id_col] = "count"
    g = work.groupby(["playlist_subgenre", "playlist_genre"], as_index=False).agg(
        agg_dict
    )
    g = g.rename(columns={id_col: "effectif"})
    return g


def _series_x(sub: pd.DataFrame, x_key: str) -> np.ndarray:
    if x_key == "acousticness_sqrt":
        return np.sqrt(np.clip(sub["acousticness"].to_numpy(dtype=float), 0, 1))
    return sub[x_key].to_numpy(dtype=float)


def _series_y(sub: pd.DataFrame, y_key: str) -> np.ndarray:
    return sub[y_key].to_numpy(dtype=float)


def _series_size(sub: pd.DataFrame, size_key: str) -> np.ndarray:
    if size_key == "effectif":
        return sub["effectif"].to_numpy(dtype=float)
    return sub[size_key].to_numpy(dtype=float)


def render(
    df: pd.DataFrame,
    x_key: str,
    y_key: str,
    size_key: str,
    top_n: int,
) -> go.Figure:
    """
    Construit la figure Plotly (bulles + packing). Paramètres d'axes / taille : clés
    colonnes ou 'acousticness_sqrt' pour l'axe X.
    """
    if df is None or df.empty:
        return _empty_fig()

    sub = _aggregate_subgenres(df)
    if sub.empty or len(sub) == 0:
        return _empty_fig("Pas de sous-genres dans la sélection")

    # Validation des clés
    if x_key == "acousticness_sqrt":
        pass
    elif x_key not in sub.columns:
        return _empty_fig("Axe X invalide")
    if y_key not in sub.columns:
        return _empty_fig("Axe Y invalide")
    if size_key not in sub.columns:
        return _empty_fig("Taille invalide")

    # Top N par popularité moyenne
    sub = sub.sort_values("track_popularity", ascending=False)
    n_keep = max(1, min(int(top_n), len(sub)))
    sub = sub.head(n_keep).reset_index(drop=True)

    need = [y_key, "acousticness"] if x_key == "acousticness_sqrt" else [y_key]
    if x_key != "acousticness_sqrt" and x_key in sub.columns:
        need.append(x_key)
    if size_key in sub.columns and size_key != "effectif":
        need.append(size_key)
    sub = sub.dropna(subset=[c for c in need if c in sub.columns])
    if sub.empty:
        return _empty_fig("Valeurs manquantes pour les axes choisis")

    n = len(sub)
    x_data = _series_x(sub, x_key)
    y_data = _series_y(sub, y_key)
    sizes_raw = _series_size(sub, size_key)

    x_min, x_max = float(np.min(x_data)), float(np.max(x_data))
    y_min, y_max = float(np.min(y_data)), float(np.max(y_data))
    x_margin = (x_max - x_min) * 0.15 + 1e-6
    y_margin = (y_max - y_min) * 0.15 + 1e-6
    x_min -= x_margin
    x_max += x_margin
    y_min -= y_margin
    y_max += y_margin

    # Rayons relatifs (taille d'encodage)
    smin, smax = float(np.min(sizes_raw)), float(np.max(sizes_raw))
    if smax <= smin:
        rel_radii = np.ones(n, dtype=float) * 0.7
    else:
        rel_radii = 0.4 + 0.6 * (sizes_raw - smin) / (smax - smin)

    W = H = 500.0
    xlo, xhi = 0.0, W
    ylo, yhi = 0.0, H
    bounds_px = (xlo, xhi, ylo, yhi)

    # Data -> pixels : carte linéaire sur tout le cadre [0,W]×[0,H] (y bas = y_min)
    dx = x_max - x_min
    dy = y_max - y_min
    if dx < 1e-12:
        x_px = np.full(n, W / 2.0)
    else:
        x_px = (x_data - x_min) / dx * W
    if dy < 1e-12:
        y_px = np.full(n, H / 2.0)
    else:
        y_px = (y_data - y_min) / dy * H

    if n == 1:
        best_scale = 42.0
        packed_x_px = x_px.copy()
        packed_y_px = y_px.copy()
    else:
        best_scale, packed_x_px, packed_y_px = _find_max_scale(
            x_px,
            y_px,
            rel_radii,
            bounds_px,
            iterations=_PACK_ITERS,
            attraction=0.004,
        )

    final_radii_px = rel_radii * best_scale
    # Diamètre Plotly (px), réduit pour mieux distinguer les points
    diameters = np.clip(
        2 * final_radii_px * _DIAM_VISUAL_SCALE,
        _MARKER_DIAM_MIN,
        _MARKER_DIAM_MAX,
    )

    # Pixels -> coords données (inverse strictement linéaire sur [x_min,x_max] × [y_min,y_max])
    px = np.clip(packed_x_px, 0.0, W)
    py = np.clip(packed_y_px, 0.0, H)
    if dx < 1e-12:
        x_packed = np.full(n, (x_min + x_max) / 2)
    else:
        x_packed = x_min + (px / W) * dx
    if dy < 1e-12:
        y_packed = np.full(n, (y_min + y_max) / 2)
    else:
        y_packed = y_min + (py / H) * dy

    genres = sub["playlist_genre"].astype(str).str.lower().to_numpy()
    labels = sub["playlist_subgenre"].astype(str).to_numpy()
    x_for_hover = x_data
    mean_pop = sub["track_popularity"].to_numpy(dtype=float)
    effectif = sub["effectif"].to_numpy(dtype=float)

    x_label = _LABELS.get(x_key, x_key)
    y_label = _LABELS.get(y_key, y_key)

    fig = go.Figure()

    # Scattergl : rendu WebGL, plus léger que des centaines de labels
    for g in np.unique(genres):
        mask = genres == g
        color = COLORS_GENRE.get(g, FALLBACK_GENRE_COLOR)
        fig.add_trace(
            go.Scattergl(
                x=x_packed[mask],
                y=y_packed[mask],
                mode="markers",
                name=g.upper(),
                legendgroup=g,
                marker=dict(
                    size=diameters[mask],
                    sizemode="diameter",
                    color=color,
                    opacity=0.9,
                    line=dict(color="rgba(255,255,255,0.28)", width=0.6),
                ),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    + f"{y_label}: %{{customdata[1]:.2f}}<br>"
                    + f"{x_label}: %{{customdata[2]:.4f}}<br>"
                    + "Effectif: %{customdata[3]}<extra></extra>"
                ),
                customdata=np.stack(
                    [
                        labels[mask],
                        mean_pop[mask],
                        x_for_hover[mask],
                        effectif[mask],
                    ],
                    axis=-1,
                ),
            )
        )

    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT_CLR, family=FONT_MONO),
        title=dict(
            text="Q5, Q7, Q8 — Popularité et signature audio par sous-genre",
            font=dict(size=11, color=TEXT_CLR),
            x=0.5,
            xanchor="center",
        ),
        margin=dict(l=44, r=8, t=40, b=56),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            x=0,
            font=dict(size=9, color=TEXT_CLR),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            title=dict(text=x_label, font=dict(color=TEXT_CLR, size=11)),
            range=[x_min, x_max],
            gridcolor=GRID_CLR,
            zeroline=False,
            tickfont=dict(size=9, color=TEXT_CLR),
            linecolor="rgba(255,255,255,0.12)",
            mirror=False,
        ),
        yaxis=dict(
            title=dict(text=y_label, font=dict(color=TEXT_CLR, size=11)),
            range=[y_min, y_max],
            gridcolor=GRID_CLR,
            zeroline=False,
            tickfont=dict(size=9, color=TEXT_CLR),
            linecolor="rgba(255,255,255,0.12)",
            mirror=False,
        ),
        hoverlabel=dict(
            bgcolor="#1a1a24",
            font_size=11,
            font_family=FONT_MONO,
        ),
        hovermode="closest",
    )

    return fig
