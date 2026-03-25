import plotly.graph_objects as go

PLACEHOLDER_STYLE = dict(
    plot_bgcolor='#0a0a0f',
    paper_bgcolor='#0a0a0f',
    font_color='#6b6b82',
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    annotations=[dict(
        text='En cours…',
        x=0.5, y=0.5,
        xref='paper', yref='paper',
        showarrow=False,
        font=dict(size=14, color='#6b6b82', family='Space Mono'),
    )],
    margin=dict(l=0, r=0, t=0, b=0),
)

def render(df):
    fig = go.Figure()
    fig.update_layout(**PLACEHOLDER_STYLE)
    return fig
