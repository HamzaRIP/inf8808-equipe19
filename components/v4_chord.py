import numpy as np
import plotly.graph_objects as go

THEME = {
    'dark': {
        'bg': '#0a0a0f', 'card': '#12121a',
        'text': '#e0e0f0', 'muted': '#6b6b82',
    },
    'light': {
        'bg': '#f5f5f0', 'card': '#e0e0d8',
        'text': '#1a1a1a', 'muted': '#888880',
    },
}

GENRE_COLORS = {
    'pop':   '#1DB954', 'rap':   '#F4A261',
    'rock':  '#E63946', 'latin': '#A8DADC',
    'r&b':   '#C77DFF', 'edm':   '#00B4D8',
}
FONT = 'Space Mono, monospace'
GAP = 0.03; R_OUT = 1.0; R_IN = 0.88; R_LABEL = 1.13


def arc_points(theta0, theta1, r=1.0, n=80):
    t = np.linspace(theta0, theta1, n)
    return r * np.cos(t), r * np.sin(t)


def bezier_ribbon(x0, y0, x1, y1, n=80):
    t = np.linspace(0, 1, n); cx, cy = 0.0, 0.0
    bx = (1-t)**3*x0 + 3*(1-t)**2*t*cx + 3*(1-t)*t**2*cx + t**3*x1
    by = (1-t)**3*y0 + 3*(1-t)**2*t*cy + 3*(1-t)*t**2*cy + t**3*y1
    return bx, by


def mid_angle(a, b): return (a + b) / 2


def rgba(hex_color, alpha):
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


def compute_layout(genres, genre_totals, co_matrix):
    total = sum(genre_totals[g] for g in genres)
    total_arc = 2 * np.pi - len(genres) * GAP
    arc_sizes = {g: (genre_totals[g] / total) * total_arc for g in genres}
    starts, ends = {}, {}; cursor = 0.0
    for g in genres:
        starts[g] = cursor; ends[g] = cursor + arc_sizes[g]; cursor = ends[g] + GAP
    ribbon_angles = {}; genre_cursors = {g: starts[g] for g in genres}
    for i, g1 in enumerate(genres):
        for j, g2 in enumerate(genres):
            if i >= j: continue
            val = co_matrix[i][j]
            if val == 0: continue
            span1 = (val / genre_totals[g1]) * arc_sizes[g1]
            a1s = genre_cursors[g1]; a1e = a1s + span1; genre_cursors[g1] = a1e
            span2 = (val / genre_totals[g2]) * arc_sizes[g2]
            a2s = genre_cursors[g2]; a2e = a2s + span2; genre_cursors[g2] = a2e
            ribbon_angles[(g1, g2)] = (a1s, a1e, a2s, a2e)
    return starts, ends, ribbon_angles


def render(df, theme: str = 'dark'):
    t = THEME.get(theme, THEME['dark'])
    MUTED = t['muted']; TEXT = t['text']; BG = t['bg']; CARD = t['card']

    subset = df[['track_id', 'playlist_genre']].drop_duplicates()
    genres_all = sorted(subset['playlist_genre'].dropna().unique().tolist())

    if len(genres_all) < 2:
        fig = go.Figure()
        fig.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG,
            annotations=[dict(text='Données insuffisantes', x=.5, y=.5,
                              xref='paper', yref='paper', showarrow=False,
                              font=dict(color=MUTED, size=13, family=FONT))],
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            margin=dict(l=0, r=0, t=0, b=0))
        return fig

    matrix_df = subset.assign(val=1).pivot_table(
        index='track_id', columns='playlist_genre',
        values='val', aggfunc='max', fill_value=0)
    genres = [g for g in genres_all if g in matrix_df.columns]
    matrix_df = matrix_df[genres]
    co_full = matrix_df.T.dot(matrix_df).values.astype(float)
    genre_totals = {g: int(matrix_df[g].sum()) for g in genres}
    co_matrix = [[int(co_full[i][j]) if i != j else 0 for j in range(len(genres))]
                 for i in range(len(genres))]
    starts, ends, ribbon_angles = compute_layout(genres, genre_totals, co_matrix)
    total_tracks = sum(genre_totals.values())
    traces = []

    for (g1, g2), (a1s, a1e, a2s, a2e) in ribbon_angles.items():
        val = co_matrix[genres.index(g1)][genres.index(g2)]
        pct1 = val / genre_totals[g1] * 100; pct2 = val / genre_totals[g2] * 100
        color = GENRE_COLORS.get(g1, '#888888')
        ax1, ay1 = arc_points(a1s, a1e, R_IN); ax2, ay2 = arc_points(a2e, a2s, R_IN)
        p1x, p1y = R_IN*np.cos(a1s), R_IN*np.sin(a1s)
        p1ex, p1ey = R_IN*np.cos(a1e), R_IN*np.sin(a1e)
        p2x, p2y = R_IN*np.cos(a2s), R_IN*np.sin(a2s)
        p2ex, p2ey = R_IN*np.cos(a2e), R_IN*np.sin(a2e)
        bx1, by1 = bezier_ribbon(p1ex, p1ey, p2x, p2y)
        bx2, by2 = bezier_ribbon(p2ex, p2ey, p1x, p1y)
        rx = np.concatenate([ax1, bx1, ax2, bx2, [ax1[0]]])
        ry = np.concatenate([ay1, by1, ay2, by2, [ay1[0]]])
        hover = (f'<b>{g1.upper()} ↔ {g2.upper()}</b><br>'
                 f'Titres partagés : <b>{val:,}</b><br>'
                 f'Part de {g1} : {pct1:.1f} %<br>Part de {g2} : {pct2:.1f} %')
        traces.append(go.Scatter(
            x=rx, y=ry, mode='lines', fill='toself',
            fillcolor=rgba(color, 0.22), line=dict(color=rgba(color, 0.5), width=0.8),
            hoverinfo='text', hovertext=hover,
            hoverlabel=dict(bgcolor=CARD, bordercolor=color,
                            font=dict(color=TEXT, family=FONT, size=12)),
            showlegend=False))

    for g in genres:
        color = GENRE_COLORS.get(g, '#888888')
        ax, ay = arc_points(starts[g], ends[g], R_OUT)
        axi, ayi = arc_points(ends[g], starts[g], R_IN)
        px = np.concatenate([ax, axi, [ax[0]]]); py = np.concatenate([ay, ayi, [ay[0]]])
        pct = genre_totals[g] / total_tracks * 100
        hover = (f'<b>{g.upper()}</b><br>Titres : <b>{genre_totals[g]:,}</b><br>'
                 f'Part du total : {pct:.1f} %')
        traces.append(go.Scatter(
            x=px, y=py, mode='lines', fill='toself',
            fillcolor=rgba(color, 0.85), line=dict(color=color, width=1.5),
            hoverinfo='text', hovertext=hover,
            hoverlabel=dict(bgcolor=CARD, bordercolor=color,
                            font=dict(color=TEXT, family=FONT, size=12)),
            showlegend=False))

    annotations = []
    for g in genres:
        angle = mid_angle(starts[g], ends[g])
        lx = R_LABEL * np.cos(angle); ly = R_LABEL * np.sin(angle)
        ca = np.cos(angle)
        align = 'left' if ca > 0.15 else ('right' if ca < -0.15 else 'center')
        annotations.append(dict(
            x=lx, y=ly,
            text=(f"<b>{g.upper()}</b><br>"
                  f"<span style='font-size:9px;color:{MUTED}'>{genre_totals[g]:,} titres</span>"),
            showarrow=False,
            font=dict(color=GENRE_COLORS.get(g, TEXT), family=FONT, size=11),
            align=align, xanchor=align, yanchor='middle'))

    fig = go.Figure(data=traces)
    fig.update_layout(
        plot_bgcolor=BG, paper_bgcolor=BG,
        font=dict(family=FONT, color=TEXT),
        xaxis=dict(visible=False, range=[-1.4, 1.4], scaleanchor='y'),
        yaxis=dict(visible=False, range=[-1.4, 1.4]),
        margin=dict(l=20, r=20, t=20, b=20),
        annotations=annotations, hovermode='closest')
    return fig
