import pandas as pd
import plotly.express as px

def store_bubble_chart(df_target, df_benchmark, df_stores, metric, metric_renamed):
    if df_target['address_id'].values[0] not in df_benchmark['address_id'].unique():
        df = pd.concat([df_benchmark, df_target])
    else:
        df = df_benchmark

    df = df.sort_values(['address_id', 'prom_wk_end_dt'], ascending=True)

    df = df.merge(df_stores, on='address_id', how='inner')

    df['year_month_dt'] = pd.to_datetime(df['prom_month_nm'].astype(str) + '-' + df['prom_year_num'].astype(str))
    df['Calendar Month'] = df['year_month_dt'].dt.strftime('%B-%y')
    df = df.groupby(['address_id', 'Store Name', 'Store Size', 'year_month_dt', 'Calendar Month'])[metric].sum().reset_index()
    df['Target or Benchmark'] = df['address_id'].apply(lambda x: 'Target Store' if x == df_target['address_id'].values[0] else 'Benchmark Store')

    def calc_metric_per_sqm(metric, store_size):
        if (metric > 0) and (store_size > 0):
            return round(metric / store_size, 2)
        else:
            return 0.001

    df[f'{metric_renamed} per sqm'] = df[[metric, 'Store Size']].apply(lambda x: calc_metric_per_sqm(*x), axis=1)
    
    df = df.rename(columns={metric: metric_renamed})
    # df = df.sort_values(['address_id', 'Calendar Month'])

    fig = px.scatter(
        data_frame=df,
        x="Store Size",
        y=metric_renamed,
        size=f"{metric_renamed} per sqm",
        size_max=30,
        hover_name="Store Name",
        animation_frame="Calendar Month",
        color="Target or Benchmark",
        color_discrete_sequence=["rgb(50, 150, 255)", "rgb(255, 128, 0)",],
        # trendline="ols",
        range_x=[min(df['Store Size']) * 0.95, max(df['Store Size']) * 1.05],
        range_y=[min(df[metric_renamed]) * 0.95, max(df[metric_renamed]) * 1.05],
    )

    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>" + \
            f"{metric_renamed}: %{{y:$.3s}}" + "<br>" + \
            "Store Size: %{x}m2" + "<br>" + \
            f"{metric_renamed} per sqm: %{{marker.size:$.0f}} per m<sup>2</sup>",
    )

    fig.update_layout(
        title=f"{metric_renamed} per m<sup>2</sup>",
        height=500,
        xaxis=dict(
            title="Store Size (m<sup>2</sup>)",
            titlefont=dict(size=15),
            tickfont_size=15,
        ),
        yaxis=dict(
            title=None,
            titlefont=dict(size=15),
            tickfont_size=15,
            tickformat="$,.2s",
        ),
        showlegend=False
    )

    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 666
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['transition'] = 666

    # Must include this section to update each new frame with the desired hovertemplate
    for f in fig.frames:
        for data in f.data:
            data.update(
                hovertemplate="<b>%{hovertext}</b><br>" + \
                f"{metric_renamed}: %{{y:$.3s}}" + "<br>" + \
                "Store Size: %{x}m2" + "<br>" + \
                f"{metric_renamed} per sqm: %{{marker.size:$.0f}} per m<sup>2</sup>"
            )
    return fig
