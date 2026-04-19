import plotly.graph_objects as go
import pandas as pd
import numpy as np

THEME = {
    'dark': {
        'bg': '#0a0a0f', 'grid': 'rgba(255,255,255,0.06)',
        'text': '#c8c8d8', 'muted': '#6b6b82',
        'connector': 'rgba(255,255,255,0.25)',
        'marker_border': '#0a0a0f',
    },
    'light': {
        'bg': '#f5f5f0', 'grid': 'rgba(0,0,0,0.08)',
        'text': '#1a1a1a', 'muted': '#888880',
        'connector': 'rgba(0,0,0,0.2)',
        'marker_border': '#f5f5f0',
    },
}

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

FONT_MONO = 'Space Mono, monospace'


def _compute_eras(df: pd.DataFrame):
    years = sorted(df['year'].dropna().unique()); n = len(years)
    if n < 10: return None
    k = max(2, int(n * 0.1))
    start = years[:k]; middle = years[n//2 - k//2 : n//2 + k//2]; end = years[-k:]
    return {
        f'{start[0]}–{start[-1]}':   (start[0],  start[-1]),
        f'{middle[0]}–{middle[-1]}': (middle[0], middle[-1]),
        f'{end[0]}–{end[-1]}':       (end[0],    end[-1]),
    }


def _era_means(df: pd.DataFrame) -> pd.DataFrame:
    ERAS = _compute_eras(df)
    if ERAS is None: return pd.DataFrame()
    rows = []
    for label, (y0, y1) in ERAS.items():
        subset = df[df['year'].between(y0, y1)]; row = {'era': label}
        for feat in FEATURES:
            row[feat] = subset[feat].mean() if feat in subset.columns and len(subset) > 0 else np.nan
        rows.append(row)
    result = pd.DataFrame(rows).set_index('era')
    if 'track_popularity' in result.columns:
        result['track_popularity'] = result['track_popularity'] / 100
    return result


def _empty_fig(msg: str = 'Données insuffisantes', t=None) -> go.Figure:
    t = t or THEME['dark']
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor=t['bg'], paper_bgcolor=t['bg'], font_color=t['muted'],
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        annotations=[dict(text=msg, x=0.5, y=0.5, xref='paper', yref='paper',
                          showarrow=False, font=dict(size=14, color=t['muted'], family=FONT_MONO))],
        margin=dict(l=0, r=0, t=0, b=0))
    return fig


def render(df: pd.DataFrame, theme: str = 'dark') -> go.Figure:
    t = THEME.get(theme, THEME['dark'])
    if df.empty: return _empty_fig(t=t)

    era_df = _era_means(df).dropna(how='all')
    if len(era_df) < 2:
        return _empty_fig('Élargissez la période pour voir les tendances.', t=t)

    era_labels = list(era_df.index); x_positions = list(range(len(era_labels)))
    fig = go.Figure()

    for feat, meta in FEATURES.items():
        y_vals = era_df[feat].tolist()
        if all(pd.isna(v) for v in y_vals): continue
        color = meta['color']; label = meta['label']
        hover_y = [f'{v:.3f}' if not pd.isna(v) else 'n/a' for v in y_vals]
        fig.add_trace(go.Scatter(
            x=x_positions, y=y_vals, mode='lines+markers', name=label,
            line=dict(color=color, width=2.5),
            marker=dict(color=color, size=10,
                        line=dict(color=t['marker_border'], width=2)),
            text=hover_y, customdata=era_labels,
            hovertemplate=(f'<b>{label}</b><br>%{{customdata}}<br>'
                           'Valeur moyenne : %{text}<extra></extra>')))

    label_positions = [(feat, era_df[feat].iloc[-1], meta)
                       for feat, meta in FEATURES.items()
                       if feat in era_df.columns and not pd.isna(era_df[feat].iloc[-1])]
    label_positions.sort(key=lambda x: x[1])

    n_labels = len(label_positions)
    y_lo, y_hi = 0.02, 0.98
    min_gap = (y_hi - y_lo) / max(n_labels, 1)  # ~0.12 for 8 labels

    adjusted = [[feat, y, meta] for feat, y, meta in label_positions]

    for i in range(1, len(adjusted)):
        if adjusted[i][1] < adjusted[i-1][1] + min_gap:
            adjusted[i][1] = adjusted[i-1][1] + min_gap

    overflow = adjusted[-1][1] - y_hi
    if overflow > 0:
        for item in adjusted:
            item[1] -= overflow

    underflow = y_lo - adjusted[0][1]
    if underflow > 0:
        for item in adjusted:
            item[1] += underflow

    label_x = x_positions[-1] + 0.55
    for (feat, real_y, meta), (_, y_adj, _) in zip(label_positions, adjusted):
        fig.add_shape(type='line', x0=x_positions[-1]+0.05, x1=label_x-0.05,
                      y0=real_y, y1=y_adj,
                      line=dict(color=t['connector'], width=1))
        fig.add_annotation(x=label_x, y=y_adj, text=meta['label'],
                           showarrow=False, font=dict(color=meta['color'], size=12, family=FONT_MONO),
                           xanchor='left')

    for xi in x_positions:
        fig.add_vline(x=xi, line_color=t['grid'], line_width=1)

    fig.update_layout(
        plot_bgcolor=t['bg'], paper_bgcolor=t['bg'],
        font=dict(color=t['text'], family=FONT_MONO, size=12),
        xaxis=dict(tickvals=x_positions, ticktext=era_labels, showgrid=False,
                   zeroline=False, range=[-0.3, len(era_labels) - 1 + 2.2],
                   fixedrange=True, tickfont=dict(color=t['text'])),
        yaxis=dict(title='Valeur moyenne', range=[-0.05, 1.1],
                   showgrid=True, gridcolor=t['grid'], zeroline=False,
                   fixedrange=True, tickfont=dict(color=t['text'])),
        legend=dict(orientation='h', x=0, y=1.08, xanchor='left', yanchor='bottom',
                    font=dict(size=11, family=FONT_MONO, color=t['text']),
                    bgcolor='rgba(0,0,0,0)', itemclick='toggleothers', itemdoubleclick='toggle'),
        hovermode='closest', margin=dict(l=60, r=220, t=70, b=48), dragmode=False)
    return fig