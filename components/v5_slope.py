import plotly.graph_objects as go
import pandas as pd
import numpy as np

FEATURES = {
    'energy':           {'label': 'Énergie',          'color': '#E24B4A'},
    'danceability':     {'label': 'Danceability',     'color': '#378ADD'},
    'valence':          {'label': 'Valence',          'color': '#EF9F27'},
    'track_popularity': {'label': 'Popularité',       'color': '#1D9E75'},
    'acousticness':     {'label': 'Acousticness',     'color': '#7F77DD'},
    'liveness':         {'label': 'Liveness',         'color': '#D4537E'},
    'speechiness':      {'label': 'Speechiness',      'color': '#63B8A0'},
    'instrumentalness': {'label': 'Instrumentalness', 'color': '#BA7517'},
}

BG         = '#0a0a0f'
GRID_CLR   = 'rgba(255,255,255,0.06)'
TEXT_CLR   = '#c8c8d8'
TEXT_MUTED = '#6b6b82'
FONT_MONO  = 'Space Mono, monospace'


def _compute_eras(df: pd.DataFrame):
    years = sorted(df['year'].dropna().unique())
    n = len(years)

    if n < 10:
        return None

    k = max(2, int(n * 0.1))

    start = years[:k]
    middle = years[n//2 - k//2 : n//2 + k//2]
    end = years[-k:]

    return {
        f"{start[0]}–{start[-1]}": (start[0], start[-1]),
        f"{middle[0]}–{middle[-1]}": (middle[0], middle[-1]),
        f"{end[0]}–{end[-1]}": (end[0], end[-1]),
    }


def _era_means(df: pd.DataFrame) -> pd.DataFrame:
    ERAS = _compute_eras(df)
    if ERAS is None:
        return pd.DataFrame()

    rows = []
    for label, (y0, y1) in ERAS.items():
        subset = df[df['year'].between(y0, y1)]
        row = {'era': label}

        for feat in FEATURES:
            if feat in subset.columns and len(subset) > 0:
                row[feat] = subset[feat].mean()
            else:
                row[feat] = np.nan

        rows.append(row)

    result = pd.DataFrame(rows).set_index('era')

    for feat in FEATURES:
        col = result[feat]
        mn, mx = col.min(), col.max()
        if mx > mn:
            result[feat] = (col - mn) / (mx - mn)
        else:
            result[feat] = 0.5

    return result


def _empty_fig(msg: str = 'Données insuffisantes') -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        font_color=TEXT_MUTED,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[dict(
            text=msg,
            x=0.5, y=0.5,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED, family=FONT_MONO),
        )],
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


def render(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_fig()

    era_df = _era_means(df)
    era_df = era_df.dropna(how='all')

    if len(era_df) < 2:
        return _empty_fig('Élargissez la période pour voir les tendances.')

    era_labels  = list(era_df.index)
    x_positions = list(range(len(era_labels)))

    fig = go.Figure()

    for feat, meta in FEATURES.items():
        y_vals = era_df[feat].tolist()

        if all(pd.isna(v) for v in y_vals):
            continue

        color = meta['color']
        label = meta['label']
        hover_y = [f'{v:.3f}' if not pd.isna(v) else 'n/a' for v in y_vals]

        fig.add_trace(go.Scatter(
            x=x_positions,
            y=y_vals,
            mode='lines+markers',
            name=label,
            line=dict(color=color, width=2.5),
            marker=dict(
                color=color,
                size=10,
                line=dict(color=BG, width=2),
            ),
            text=hover_y,
            customdata=era_labels,
            hovertemplate=(
                f'<b>{label}</b><br>'
                '%{customdata}<br>'
                'Valeur normalisée : %{text}'
                '<extra></extra>'
            ),
        ))

    label_positions = []

    for feat, meta in FEATURES.items():
        if feat in era_df.columns:
            val = era_df[feat].iloc[-1]
            if not pd.isna(val):
                label_positions.append((feat, val, meta))

    label_positions.sort(key=lambda x: x[1])

    min_gap = 0.06
    adjusted = []

    for feat, y, meta in label_positions:
        if not adjusted:
            adjusted.append([feat, y, meta])
        else:
            prev_y = adjusted[-1][1]
            new_y = max(y, prev_y + min_gap)
            adjusted.append([feat, new_y, meta])

    overflow = adjusted[-1][1] - 0.98
    if overflow > 0:
        for i in range(len(adjusted)):
            adjusted[i][1] -= overflow

    label_x = x_positions[-1] + 0.8

    for (feat, real_y, meta), (_, y_adj, _) in zip(label_positions, adjusted):

        fig.add_shape(
            type="line",
            x0=x_positions[-1] + 0.05,
            x1=label_x - 0.05,
            y0=real_y,
            y1=y_adj,
            line=dict(color='rgba(255,255,255,0.25)', width=1)
        )

        fig.add_annotation(
            x=label_x,
            y=y_adj,
            text=meta['label'],
            showarrow=False,
            font=dict(color=meta['color'], size=12, family=FONT_MONO),
            xanchor='left',
        )

    fig.update_layout(
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        font=dict(color=TEXT_CLR, family=FONT_MONO, size=12),

        xaxis=dict(
            tickvals=x_positions,
            ticktext=era_labels,
            showgrid=False,
            zeroline=False,
            range=[-0.3, len(era_labels) - 1 + 2],
            fixedrange=True,
        ),

        yaxis=dict(
            title='Valeur normalisée (0 – 1)',
            range=[-0.05, 1.1],
            showgrid=True,
            gridcolor=GRID_CLR,
            zeroline=False,
            fixedrange=True,
        ),

        legend=dict(
            orientation='h',
            x=0,
            y=1.08,
            xanchor='left',
            yanchor='bottom',
            font=dict(size=11, family=FONT_MONO, color=TEXT_CLR),
            bgcolor='rgba(0,0,0,0)',
            itemclick='toggleothers',
            itemdoubleclick='toggle',
        ),

        hovermode='closest',
        margin=dict(l=60, r=180, t=70, b=48),
        dragmode=False,
    )

    fig.add_annotation(
        x=0,
        y=1.18,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=11, color=TEXT_MUTED, family=FONT_MONO),
    )

    for xi in x_positions:
        fig.add_vline(x=xi, line_color=GRID_CLR, line_width=1)

    return fig