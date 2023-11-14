import pandas as pd
import plotly.graph_objects as go


def create_df_indexed_metric(df, metric, metric_renamed, st_ss_agg_method, cumsum=False):
    if st_ss_agg_method == 'Sum of Stores':
        df = df.groupby('prom_wk_end_dt')[metric].sum().reset_index()
    elif st_ss_agg_method == 'Average per Store':
        df = df.groupby('prom_wk_end_dt')[metric].mean().reset_index()
    df = df.rename(columns={'prom_wk_end_dt': 'Week', metric: metric_renamed})
    df = df.sort_values(['Week'], ascending=True)

    if cumsum is True:
        # Cumulative Sum - Index starting value = 100
        df['Cum Sum'] = df[metric_renamed].cumsum()
        idx_val = df['Cum Sum'].values[0]
        df[f'Cumulative {metric_renamed} Indexed'] = df['Cum Sum'].apply(lambda x: round((x/idx_val * 100), 0)).astype(int)
        df = df.drop('Cum Sum', axis=1)
    else:
        # Indexed starting value = 100
        idx_val = df[metric_renamed].values[0]
        df[f'{metric_renamed} Indexed'] = df[metric_renamed].apply(lambda x: round((x/idx_val * 100), 0)).astype(int)
    
    return df.drop(metric_renamed, axis=1)


def indexed_comps_chart(df_target, df_benchmark):
    metric_target = df_target.columns[1]
    metric_benchmark = df_benchmark.columns[1]
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            name=f"Target Store {metric_target}",
            x=df_target['Week'], 
            y=df_target[metric_target].fillna(''),
            mode='lines',
            showlegend=True,
            hovertemplate=f"Target Store {metric_target}: %{{y:.3s}}<extra></extra>",    # Double curly braces because the outside {} escapes the inner {}
            line_shape='spline',
            marker_color='rgb(255, 128, 0)'
        )
    )
    fig.add_trace(
        go.Scatter(
            name=f"Benchmark {metric_benchmark}",
            x=df_benchmark['Week'], 
            y=df_benchmark[metric_benchmark].fillna(''),
            mode='lines',
            showlegend=True,
            hovertemplate=f"Benchmark {metric_benchmark}: %{{y:.3s}}<extra></extra>",    # Double curly braces because the outside {} escapes the inner {}
            line_shape='spline',
            marker_color="#2979bf"
        )
    )
    # -------------------------- Configure Layout ---------------------- #
    fig.update_layout(
        height=333,
        title=f"{metric_target} - Weekly",
        xaxis=dict(tickfont_size=16),
        yaxis=dict(
            tickfont_size=16,
            # color='#C0C0C0',
            ),
        hovermode='x unified',
        legend=dict(
            font=dict(
                size=12
            ),
            orientation='h',
            yanchor='bottom',
            xanchor='right',
            x=1.0,
            y=1.0,
        ),
        margin=dict(t=33, b=33),
    )
    return fig
