import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_df_target_store(df, target_address_id):
    df_shelf_sales_target_store = df[df['address_id'] == target_address_id][[
        'wk_start_dt', 'month_nm', 'month_num', 'year_num', 'shelf_sales_ex_gst', 'total_store_sales_ex_gst'
    ]].reset_index(drop=True)
    df_shelf_sales_target_store['wk_start_dt'] = pd.to_datetime(df_shelf_sales_target_store['wk_start_dt'])
    df_shelf_sales_target_store['shelf_sales_pct'] = \
        df_shelf_sales_target_store['shelf_sales_ex_gst'] / df_shelf_sales_target_store['total_store_sales_ex_gst']
    return df_shelf_sales_target_store


def create_df_benchmark_stores(df, benchmark_address_ids, agg_method='mean'):
    df_benchmark_stores = df[df['address_id'].isin(benchmark_address_ids)]
    store_count = len(df_benchmark_stores['address_id'].unique())
    df_shelf_sales_benchmark_stores = df_benchmark_stores[[
        'wk_start_dt', 'month_nm', 'month_num', 'year_num', 'shelf_sales_ex_gst', 'total_store_sales_ex_gst'
    ]].groupby([
        'wk_start_dt', 'month_nm', 'month_num', 'year_num'
    ]).sum(['shelf_sales_ex_gst', 'total_store_sales_ex_gst']).reset_index().sort_values('wk_start_dt')
    df_shelf_sales_benchmark_stores['wk_start_dt'] = pd.to_datetime(df_shelf_sales_benchmark_stores['wk_start_dt'])
    if agg_method == 'mean':
        df_shelf_sales_benchmark_stores[['shelf_sales_ex_gst', 'total_store_sales_ex_gst']] = \
            df_shelf_sales_benchmark_stores[['shelf_sales_ex_gst', 'total_store_sales_ex_gst']] / store_count
    df_shelf_sales_benchmark_stores['shelf_sales_pct'] = \
        df_shelf_sales_benchmark_stores['shelf_sales_ex_gst'] / df_shelf_sales_benchmark_stores['total_store_sales_ex_gst']
    return df_shelf_sales_benchmark_stores


def create_df_target_store_idx(df, target_address_id):
    benchmark_column_nm = df.columns[df.columns.str.contains('benchmark')].values[0]
    df_target_store_shelf_idx = df[df['address_id'] == target_address_id][[
        'wk_start_dt', 'month_nm', 'month_num', 'year_num', 'store_sales_inc_gst', benchmark_column_nm]].reset_index(drop=True)
    df_target_store_shelf_idx['wk_start_dt'] = pd.to_datetime(df_target_store_shelf_idx['wk_start_dt'])
    df_target_store_shelf_idx['price_index'] = \
        round(df_target_store_shelf_idx['store_sales_inc_gst'] / df_target_store_shelf_idx[benchmark_column_nm], 4) * 100
    return df_target_store_shelf_idx


def create_df_benchmark_stores_idx(df, benchmark_address_ids, agg_method='mean'):
    benchmark_column_nm = df.columns[df.columns.str.contains('benchmark')].values[0]
    df_benchmark_stores_idx = df[df['address_id'].isin(benchmark_address_ids)]
    store_count = len(df_benchmark_stores_idx['address_id'].unique())
    df_benchmark_stores_idx = df_benchmark_stores_idx[[
        'wk_start_dt', 'month_nm', 'month_num', 'year_num', 'store_sales_inc_gst', benchmark_column_nm
    ]].groupby([
        'wk_start_dt', 'month_nm', 'month_num', 'year_num'
    ]).sum(['store_sales_inc_gst', benchmark_column_nm]).reset_index().sort_values('wk_start_dt')
    df_benchmark_stores_idx['wk_start_dt'] = pd.to_datetime(df_benchmark_stores_idx['wk_start_dt'])
    if agg_method == 'mean':
        df_benchmark_stores_idx[['store_sales_inc_gst', benchmark_column_nm]] = \
            df_benchmark_stores_idx[['store_sales_inc_gst', benchmark_column_nm]] / store_count
    df_benchmark_stores_idx['price_index'] = \
        round(df_benchmark_stores_idx['store_sales_inc_gst'] / df_benchmark_stores_idx[benchmark_column_nm], 4) * 100
    return df_benchmark_stores_idx


def weekly_shelf_sales_chart(df_shelf, df_price_idx):
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03
    )
    # --------------------------- Shelf Sales ex GST ------------------------- #
    fig.add_trace(
        go.Bar(
            name="Shelf Sales ex GST",
            x=df_shelf['wk_start_dt'], 
            y=df_shelf['shelf_sales_ex_gst'],
            marker_color='rgb(0, 84, 165)',
            showlegend=True,
            hovertemplate="Shelf Sales: %{y:$,.2f}<extra></extra>",    # Double curly braces because the outside {} escapes the inner {}
            # line_shape="spline",
        )
    )
    # ---------------------------- Shelf Sales as % of Total Sales (ex GST) ------------------------- #
    fig.add_trace(
        go.Scatter(
            name="Shelf Sales as % of Total Sales (ex GST)",
            x=df_shelf['wk_start_dt'], 
            y=df_shelf['shelf_sales_pct'],
            marker_color='rgb(15, 187, 233)',
            mode="lines+markers",
            showlegend=True,
            hovertemplate="Shelf Sales % of Total : %{y:.2%}<extra></extra>",
            line_shape="hvh",
            xaxis="x2",
            yaxis="y2"
        )
    )
    # ---------------------------- Shelf Sales Price Index ------------------------- #
    fig.add_trace(
        go.Scatter(
            name="Shelf vs IGA Base Price Index",
            x=df_price_idx['wk_start_dt'], 
            y=df_price_idx['price_index'],
            marker_color='rgb(255, 145, 0)',
            mode="lines+markers",
            showlegend=True,
            hovertemplate="Shelf vs IGA Base Price Index : %{y:,.2f}<extra></extra>",
            # line_shape="hvh",
            xaxis="x3",
            yaxis="y3"
        )
    )
    # -------------------------- Configure Layout ---------------------- #
    fig.update_layout(
        height=999,
        title="Shelf Sales & Shelf as % of Total Sales (ex GST) - Weekly",
        yaxis_title="Shelf Sales ex GST",
        yaxis2_title="Shelf as % of Total",
        yaxis3_title="Price Index vs IGA Base",
        xaxis=dict(
            tickfont_size=14,
            tickmode="array",
            tickvals=df_shelf['wk_start_dt'],
            ticktext=df_shelf['wk_start_dt'].dt.strftime('%d %b %Y'),
        ),
        yaxis=dict(
            tickfont_size=14,
            tickformat="$,.0s",
            showspikes=True,
            color="#C0C0C0",
            # domain=[0.33, 1]
            ),
        xaxis2=dict(
            tickmode="array",
            tickvals=df_shelf['wk_start_dt'],
            ticktext=df_shelf['wk_start_dt'].dt.strftime('%d %b %Y'),
            tickfont_size=14,
            showspikes=True,
            color="#C0C0C0"
        ),
        yaxis2=dict(
            tickfont_size=14,
            tickformat=",.0%",
            showspikes=True,
            color="#C0C0C0",
            # domain=[0, 0.33]
            ),
        xaxis3=dict(
            tickmode="array",
            tickvals=df_price_idx['wk_start_dt'],
            ticktext=df_price_idx['wk_start_dt'].dt.strftime('%d %b %Y'),
            tickfont_size=14,
            showspikes=True,
            color="#C0C0C0"
        ),
        yaxis3=dict(
            tickfont_size=14,
            # dtick=0.5,
            # tickformat=",.0%",
            showspikes=True,
            # color="#C0C0C0",
            # domain=[0, 0.33]
            ),
        hovermode="x unified",
        legend=dict(
            font=dict(
                size=12
            ),
            orientation="h",
            yanchor="bottom",
            xanchor="right",
            x=1.0,
            y=1.0,
        )
    )
    # ----------- Extends the hover line across both subplots ------------ #
    fig.update_traces(xaxis="x3")

    return fig


def weekly_comp_idx_chart(df_wow_bof_np_idx, df_col_bof_np_idx):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05
    )
    # ---------------------------- WOW BOF Price Index ------------------------- #
    fig.add_trace(
        go.Scatter(
            name="WOW BOF (Non-promo) Price Index",
            x=df_wow_bof_np_idx['wk_start_dt'], 
            y=df_wow_bof_np_idx['price_index'],
            marker_color='rgb(0, 151, 88)',
            mode="lines+markers",
            showlegend=True,
            hovertemplate="WOW BOF (Non-promo) Price Index : %{y:,.2f}<extra></extra>",
        )
    )
    # ---------------------------- COL BOF Price Index ------------------------- #
    fig.add_trace(
        go.Scatter(
            name="COL BOF (Non-promo) Price Index",
            x=df_col_bof_np_idx['wk_start_dt'], 
            y=df_col_bof_np_idx['price_index'],
            marker_color='rgb(235, 30, 24)',
            mode="lines+markers",
            showlegend=True,
            hovertemplate="COL BOF (Non-promo) Price Index : %{y:,.2f}<extra></extra>",
            xaxis="x2",
            yaxis="y2",            
        )
    )
    # -------------------------- Configure Layout ---------------------- #
    fig.update_layout(
        height=666,
        title="Price Index vs Competitors (Non-promo) - Weekly",
        xaxis=dict(
            tickfont_size=14,
            tickmode="array",
            tickvals=df_wow_bof_np_idx['wk_start_dt'],
            ticktext=df_wow_bof_np_idx['wk_start_dt'].dt.strftime('%d %b %Y'),
        ),
        yaxis=dict(
            tickfont_size=14,
            # dtick=5,
            # tickformat="$,.0s",
            showspikes=True,
            color="#C0C0C0",
            # domain=[0.33, 1]
            ),
        xaxis2=dict(
            tickmode="array",
            tickvals=df_col_bof_np_idx['wk_start_dt'],
            ticktext=df_col_bof_np_idx['wk_start_dt'].dt.strftime('%d %b %Y'),
            tickfont_size=14,
            showspikes=True,
            color="#C0C0C0"
        ),
        yaxis2=dict(
            tickfont_size=14,
            # dtick=5,
            # tickformat=",.0%",
            showspikes=True,
            color="#C0C0C0",
            # domain=[0, 0.33]
            ),
        hovermode="x unified",
        legend=dict(
            font=dict(
                size=12
            ),
            orientation="h",
            yanchor="bottom",
            xanchor="right",
            x=1.0,
            y=1.0,
        )
    )
    # ----------- Extends the hover line across both subplots ------------ #
    fig.update_traces(xaxis="x2")

    return fig
