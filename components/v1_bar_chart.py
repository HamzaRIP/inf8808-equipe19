import pandas as pd
import plotly.graph_objects as go
import numpy as np



def render(df):
    feature_cols = [
        'acousticness',
        'danceability',
        'loudness',
        'valence',
        'mode',
        'speechiness',
        'key',
        'tempo',
        'liveness',
        'energy',
        'duration_ms',
        'instrumentalness'
    ]

    target_col = 'track_popularity'
    available_features = [col for col in feature_cols if col in df.columns]

    if target_col not in df.columns or not available_features:
        fig = go.Figure()
        fig.update_layout(**PLACEHOLDER_STYLE)
        return fig

    corr = df[available_features + [target_col]].corr(numeric_only=True)[target_col]
    corr = corr.drop(target_col).sort_values(ascending=False)

    label_map = {
        'acousticness': 'Acousticness',
        'danceability': 'Danceability',
        'loudness': 'Loudness',
        'valence': 'Valence',
        'mode': 'Mode',
        'speechiness': 'Speechiness',
        'key': 'Key',
        'tempo': 'Tempo',
        'liveness': 'Liveness',
        'energy': 'Energy',
        'duration_ms': 'Duration',
        'instrumentalness': 'Instrumentalness'
    }

    labels = [label_map.get(col, col) for col in corr.index]
    final_values = corr.values
    colors = ['#22c55e' if v > 0 else '#b3b3b3' for v in final_values]

    fig = go.Figure(
        data=[
            go.Bar(
                x=np.zeros_like(final_values),
                y=labels,
                orientation='h',
                marker=dict(color=colors),
                hovertemplate='<b>%{y}</b><br>Correlation: %{x:.2f}<extra></extra>'
            )
        ],
        frames=[
            go.Frame(
                data=[
                    go.Bar(
                        x=final_values,
                        y=labels,
                        orientation='h',
                        marker=dict(color=colors)
                    )
                ]
            )
        ]
    )

    fig.update_layout(
        plot_bgcolor='#0a0a0f',
        paper_bgcolor='#0a0a0f',
        font=dict(color='white', family='Arial'),
        title=dict(
            text='Which Spotify Audio Features Correlate with Track Popularity?',
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='white')
        ),
        margin=dict(l=170, r=80, t=70, b=70),
        xaxis=dict(
            showgrid=False,
            zeroline=True,
            zerolinecolor='#6f6f6f',
            zerolinewidth=2,
            tickfont=dict(color='white'),
            range=[
                min(final_values.min() - 0.1, -0.1),
                max(final_values.max() + 0.1, 0.1)
            ]
        ),
        yaxis=dict(
            tickfont=dict(color='white'),
            autorange='reversed',
            automargin=True,
            ticklabelposition='outside'
        ),
        showlegend=False,
        bargap=0.35,
        transition=dict(duration=1200, easing='cubic-in-out'),
        updatemenus=[
            dict(
                type='buttons',
                showactive=False,
                x=0.98,
                y=0.02,
                xanchor='right',
                yanchor='bottom',
                direction='left',
                bgcolor='rgba(10,10,15,0.85)',
                bordercolor='white',
                borderwidth=1,
                pad=dict(r=8, t=8, l=8, b=8),
                buttons=[
                    dict(
                        label='▶ View',
                        method='animate',
                        args=[
                            None,
                            dict(
                                frame=dict(duration=1200, redraw=True),
                                transition=dict(duration=1200, easing='cubic-in-out'),
                                fromcurrent=True
                            )
                        ]
                    )
                ]
            )
        ]
    )

    return fig
