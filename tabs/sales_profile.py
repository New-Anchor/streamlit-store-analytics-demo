import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_option_menu import option_menu
from charts.shelf_price_idx_charts import *
from datetime import datetime


def render_no_data_warning():
    st.warning('Please select a target store in the **Store Selection** tab')


# Read Parquet - Cached
def render_page():
    t0 = datetime.now()
    # -------- Sidebar -------- #
    st.sidebar.markdown(
        f"""
        **Target Store:**

        {st.session_state['store_nm_selected']} 
        
        {st.session_state['target_store_chanzfp']}

        {st.session_state['target_store_state']}

        **No. of Benchmark Stores:** 
        
        {len(st.session_state['benchmark_address_ids'])}
        """
    )
    
    # ---------------------------- Load Data Parquet Query ---------------------------- #
    """
    Add target store address id with benchmark address ids to get the complete list of 
    address ids needed. Use set(list(x)) to remove duplicates in the event target store 
    is included in the benchmark. This list is then used as a filter in the read_parquet 
    function. Finally, Split into target and benchmark dataframes.
    """
    address_list = list(set(st.session_state['benchmark_address_ids']))
    address_list.append(st.session_state['target_address_id'])
    address_list = list(set(address_list))
    
    datasource = r"data/sales_profile_weekly.parquet"
    
    address_filter = [('address_id', 'in', address_list)]
    
    @st.cache_data
    def load_data(data, address_filter):
        return pd.read_parquet(data, filters=address_filter)
    
    # ---------------------------- Initialize Dataframes ---------------------------- #
    data = load_data(datasource, address_filter)
    data['prom_mth_yr_dt'] = pd.to_datetime(data['prom_month_nm'].astype(str) + data['prom_year_num'].astype(str), format='%B%Y')
    data['lped_qtr_yr_dt'] = data['lped_qtr_nm'].str[:2] + '-' + data['lped_year_num'].astype(str)
    data['prom_wk_end_dt'] = pd.to_datetime(data['prom_wk_end_dt']).dt.date
    min_dt = min(data['prom_wk_end_dt'])
    max_dt = max(data['prom_wk_end_dt'])
    if 'sales_profile_start_dt' not in st.session_state:
        st.session_state['sales_profile_start_dt'] = min_dt
    if 'sales_profile_end_dt' not in st.session_state:
        st.session_state['sales_profile_end_dt'] = max_dt
    
    df_target_store = data[data['address_id'] == st.session_state['target_address_id']]
    df_benchmark_stores = data[data['address_id'].isin(st.session_state['benchmark_address_ids'])]
    
    # -------- Top of page -------- #
    st.header("Sales Profile")

    # ------------------------------ Filters ------------------------------ #
    with st.expander(label="**Settings**", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            measure_types = ["Sales ex GST", "Gross Profit ex GST",]
            if "measure_type" not in st.session_state:
                st.session_state['measure_type'] = measure_types[0]

            def measure_type_callback():
                st.session_state['measure_type'] = st.session_state['new_measure_type']
                
            st.selectbox(
                label="**Measure Type**",
                help="_Choose between Sales, Gross Profit and Units._",
                options=measure_types,
                index=measure_types.index(st.session_state['measure_type']),
                key="new_measure_type",
                on_change=measure_type_callback,
            )

        with col2:
            chart_mode_types = ["Weekly", "Monthly"]
            if "synoptic_periodicity" not in st.session_state:
                st.session_state['synoptic_periodicity'] = chart_mode_types[0]
                
            def chart_mode_idx_callback():
                st.session_state["synoptic_periodicity"] = st.session_state["new_synoptic_periodicity"]
                
            st.selectbox(
                label="**Periodicity**",
                help="_**N.B.** - First LPED Quarter is REMOVED in YoY Quarterly (LPED). The reason is because it's not a full quarter and it is part of the PREVIOUS year's LPED quarter._",
                options=chart_mode_types,
                index=chart_mode_types.index(st.session_state["synoptic_periodicity"]),
                key="new_synoptic_periodicity",
                on_change=chart_mode_idx_callback,
            )
            
        with col3:
            promo_status_types = ["Promo & Non-Promo", "Non-Promo Only", "Promo Only"]
            if "promotion_ind" not in st.session_state:
                st.session_state['promotion_ind'] = promo_status_types[0]
                
            def promo_selection_idx_callback():
                st.session_state['promotion_ind'] = st.session_state['new_promotion_ind']
                
            st.selectbox(
                label="**Promotion Status**",
                help="_Synoptics calls this Lead in/Lead out ._",
                options=promo_status_types, 
                index=promo_status_types.index(st.session_state['promotion_ind']),
                key="new_promotion_ind",
                on_change=promo_selection_idx_callback,
            )
        
        if st.session_state['promotion_ind'] == "Non-Promo Only":
            df_target_store = df_target_store[df_target_store['promotion_ind'] == "N"]
            df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['promotion_ind'] == "N"]
        elif st.session_state['promotion_ind'] == "Promo Only":
            df_target_store = df_target_store[df_target_store['promotion_ind'] == "Y"]
            df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['promotion_ind'] == "Y"]
            
        col1, col2 = st.columns(2)
        with col1:
            def start_dt_callback():
                st.session_state['sales_profile_start_dt'] = st.session_state['sales_profile_new_start_dt']
            st.date_input(
                label="**Start Date**",
                help="_**N.B.** - Choose the appropriate Tuesday (prom week end date) with regards to the Implementation Date_",
                value=st.session_state['sales_profile_start_dt'],
                min_value=min_dt,
                max_value=max_dt,
                key='sales_profile_new_start_dt',
                on_change=start_dt_callback
            )
            
        with col2:
            def end_dt_callback():
                st.session_state['sales_profile_end_dt'] = st.session_state['sales_profile_new_end_dt']
            st.date_input(
                label="**End Date**",
                help="_**N.B.** - Choose the appropriate Tuesday (prom week end date) with regards to the Implementation Date_",
                value=st.session_state['sales_profile_end_dt'],
                min_value=min_dt,
                max_value=max_dt,
                key='sales_profile_new_end_dt',
                on_change=end_dt_callback
            )
        
        df_target_store = df_target_store[df_target_store['prom_wk_end_dt'].between(st.session_state['sales_profile_start_dt'], st.session_state['sales_profile_end_dt'])]
        df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['prom_wk_end_dt'].between(st.session_state['sales_profile_start_dt'], st.session_state['sales_profile_end_dt'])]
        
        
        media_plc_options = df_benchmark_stores['media_plc'].sort_values(ascending=True).unique().tolist()
        if 'media_plc_filter' not in st.session_state:
            st.session_state['media_plc_filter'] = media_plc_options
        
        def callback_media_plc_filter():
            st.session_state['media_plc_filter'] = st.session_state['new_media_plc_filter']

        st.multiselect(
            label="**Classification Filter**",
            options=media_plc_options,
            default=st.session_state['media_plc_filter'],
            key="new_media_plc_filter",
            on_change=callback_media_plc_filter
        )

        df_target_store = df_target_store[df_target_store['media_plc'].isin(st.session_state['media_plc_filter'])]
        df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['media_plc'].isin(st.session_state['media_plc_filter'])]

        PERIOD_COL_DICT = {'Weekly': 'prom_wk_end_dt', 'Monthly': 'prom_mth_yr_dt', 'Quarterly (LPED)': 'lped_qtr_yr_dt'}
        PERIOD = PERIOD_COL_DICT[st.session_state["synoptic_periodicity"]]
        METRIC_COL_DICT = {'Sales ex GST': 'sales_ex_gst', 'Gross Profit ex GST': 'gp_ex_gst', 'Units': 'sales_qty'}
        METRIC = METRIC_COL_DICT[st.session_state["measure_type"]]

        def make_df_synoptics(df, synoptic_periodicity):
            df = df.groupby(['media_plc', PERIOD])[['sales_ex_gst', 'gp_ex_gst', 'sales_qty']].sum().reset_index()
            df_total = df.groupby([PERIOD])[['sales_ex_gst', 'gp_ex_gst', 'sales_qty']].sum().reset_index()
            df_total = df_total.rename(columns={'sales_ex_gst': 'total_sales_ex_gst', 'gp_ex_gst': 'total_gp_ex_gst', 'sales_qty': 'total_sales_qty'})
            df = pd.merge(df, df_total, on=PERIOD, how='inner')
            df['sales_ex_gst_pct_total'] = df['sales_ex_gst'] / df['total_sales_ex_gst']
            df['gp_ex_gst_pct_total'] = df['gp_ex_gst'] / df['total_gp_ex_gst']
            df['sales_qty_pct_total'] = df['sales_qty'] / df['total_sales_qty']
            return df

        
        df_target_store = make_df_synoptics(df_target_store, st.session_state["synoptic_periodicity"])
        df_benchmark_stores = make_df_synoptics(df_benchmark_stores, st.session_state["synoptic_periodicity"])


        def stacked_bar_chart(df):
            fig = px.bar(
                data_frame=df.sort_values(METRIC, ascending=False), 
                x=PERIOD, 
                y=METRIC,
                color="media_plc",
                # text="media_plc",
                custom_data=["media_plc", f"total_{METRIC}", f"{METRIC}_pct_total"],  
                title=f'{st.session_state["measure_type"]} - {st.session_state["synoptic_periodicity"]}',
                height=500,
                template='none'
            )
            if st.session_state["synoptic_periodicity"] == "Weekly":
                hover_period = "Prom Week End Date "
            elif st.session_state["synoptic_periodicity"] == "Monthly":
                hover_period = "Month"
            fig.update_traces(
                hoverinfo="none",
                hovertemplate="<br>".join([
                    "<b>%{customdata[0]}</b><br>",
                    f"{hover_period}: %{{x}}",
                    f"{st.session_state['measure_type']}: %{{y:$,.3s}}",
                    f"Percentage of Total {st.session_state['measure_type']}: %{{customdata[2]:.1%}}",
                    f"Total {st.session_state['measure_type']} for Period: %{{customdata[1]:$,.3s}}",
                ]),
            )
            if st.session_state["synoptic_periodicity"] == 'Weekly':
                x_tickformat = "%Y-%b-%d"
                x_tickvals = None
            else:
                x_tickformat = "%b-%Y"
                x_tickvals = None   
            fig.update_layout(
                yaxis_title=None,
                xaxis_title=None,
                legend_title="Classification",
                xaxis=dict(
                    tickfont_size=14,
                    tickvals=x_tickvals,
                    tickformat=x_tickformat,
                    # color="#C0C0C0",
                ),
                yaxis=dict(
                    tickfont_size=14,
                    tickformat="$,.0s",
                    # color="#C0C0C0",
                ),
                hovermode='closest',
                margin=dict(t=33, b=33),
            )
            return fig

        
        def pct_total_line_chart(df):
            fig = px.line(
                data_frame=df, 
                x=PERIOD, 
                y=f'{METRIC}_pct_total',
                color='media_plc',
                custom_data=["media_plc"],
                title=f'{st.session_state["measure_type"]} - {st.session_state["synoptic_periodicity"]} - % of Total', 
                height=555,
                template='none'
            )
            if st.session_state["synoptic_periodicity"] == "Weekly":
                hover_period = "Prom Week End Date "
            elif st.session_state["synoptic_periodicity"] == "Monthly":
                hover_period = "Month"
            fig.update_traces(
                hoverinfo="none",
                hovertemplate="<br>".join([
                    "<b>%{customdata[0]}</b><br>",
                    f"{hover_period}: %{{x}}",
                    f"Percentage of Total {st.session_state['measure_type']} for Period: %{{y:,.1%}}",
                ]),
            )
            if st.session_state["synoptic_periodicity"] == 'Weekly':
                x_tickformat = "%Y-%b-%d"
            else:
                x_tickformat = "%b-%Y"
            fig.update_layout(
                yaxis_title=None,
                xaxis_title=None,
                legend_title="Classification",
                # hovermode="x",
                margin=dict(t=33, b=33),
                xaxis=dict(
                    tickfont_size=14,
                    tickformat=x_tickformat,
                    showspikes=True,
                    spikesnap="cursor", 
                    spikemode="across",
                ),
                yaxis=dict(
                    tickfont_size=14,
                    tickformat=",.0%",
                    showspikes=True,
                    spikesnap="cursor", 
                    spikemode="across",
                )
            )
            return fig

        
    # ----------------------------------------------- Horizontal View Selector ----------------------------------------------- #
    view_option_list = ["Target Store", "Target Store vs Benchmark Group", "Benchmark Group"]

    if "default_option_menu_idx" not in st.session_state:
        st.session_state["default_option_menu_idx"] = 0

    def callback_option_menu(key):
        st.session_state["default_option_menu_idx"] = view_option_list.index(st.session_state[key])

    view_option = option_menu(
        menu_title=None,
        options=view_option_list,
        icons=["bar-chart", "window-split", "bar-chart-fill"],
        orientation='horizontal',
        key="view_option",
        default_index=st.session_state["default_option_menu_idx"],
        on_change=callback_option_menu,
        styles={
            "container": {
                "max-width": "None !important",
                "font-size": "15px"
            }
        }
    )
    
    if view_option == "Target Store":
        st.plotly_chart(stacked_bar_chart(df_target_store), use_container_width=True)
        st.plotly_chart(pct_total_line_chart(df_target_store), use_container_width=True)

        with st.expander(label="View Data", expanded=False):
            st.dataframe(df_target_store, use_container_width=True)
            st.download_button(
                label="Download Data", 
                data=df_target_store.to_csv(index=False),
                file_name=f"{st.session_state['store_nm_selected']} {st.session_state['measure_type']}.csv"
            )
    elif view_option == "Benchmark Group":
        st.plotly_chart(stacked_bar_chart(df_benchmark_stores), use_container_width=True)
        st.plotly_chart(pct_total_line_chart(df_benchmark_stores), use_container_width=True)

        with st.expander(label="View Data", expanded=False):
            st.dataframe(df_benchmark_stores, use_container_width=True)
            st.download_button(
                label="Download Data", 
                data=df_benchmark_stores.to_csv(index=False),
                file_name=f"{st.session_state['store_nm_selected']} {st.session_state['measure_type']}.csv"
            )
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(stacked_bar_chart(df_target_store), use_container_width=True)
            st.plotly_chart(pct_total_line_chart(df_target_store), use_container_width=True)
        with col2:
            st.plotly_chart(stacked_bar_chart(df_benchmark_stores), use_container_width=True)
            st.plotly_chart(pct_total_line_chart(df_benchmark_stores), use_container_width=True)


    st.write(datetime.now() - t0)
