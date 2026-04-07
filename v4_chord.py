import plotly.graph_objects as go

DARK  = dict(bg='#0a0a0f', paper='#0a0a0f', font='#6b6b82')
LIGHT = dict(bg='#f5f5f0', paper='#f5f5f0', font='#888880')

def render(df, theme='dark'):
    t = LIGHT if theme == 'light' else DARK
    fig = go.Figure()
    fig.update_layout(
        plot_bgcolor=t['bg'],
        paper_bgcolor=t['paper'],
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
        margin=dict(l=0, r=0, t=0, b=0),
        annotations=[dict(
            text='V4 — Chord Diagram (Noah)',
            x=0.5, y=0.5,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=13, color=t['font'], family='Space Mono'),
        )],
    )
    return fig
