import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from charts.chart_tools import *
from datetime import datetime


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

    datasource = r"data/baskets_weekly.parquet"
    
    address_filter = [('address_id', 'in', address_list)]
    
    @st.cache_data
    def load_baskets_data(data, address_filter):
        return pd.read_parquet(data, filters=address_filter)

    # ---------------------------- Initialize Dataframes ---------------------------- #
    data = load_baskets_data(datasource, address_filter)
    data['prom_mth_yr_dt'] = pd.to_datetime(data['prom_mth_num'].astype(str) + data['prom_year_num'].astype(str), format='%m%Y')
    data['lped_qtr_yr_dt'] = data['lped_qtr_nm'].str[:2] + '-' + data['lped_year_num'].astype(str)
    
    df_target_store = data[data['address_id'] == st.session_state['target_address_id']]
    df_benchmark_stores = data[data['address_id'].isin(st.session_state['benchmark_address_ids'])]

    # ------------------------------ Page Top ------------------------------ #
    st.header("**Baskets** 🛒")
    
    # ------------------------------ Filters ------------------------------ #
    with st.expander(label="**Settings**", expanded=True):
        # col1, col2 = st.columns(2)
        
        # with col1:
        
            chart_mode_types = ["YoY - Quarterly", "YoY - Monthly", "YoY - Weekly", "Quarterly", "Monthly", "Weekly"]

            if "periodicity" not in st.session_state:
                st.session_state['periodicity'] = chart_mode_types[-1]

            def chart_mode_idx_callback():
                st.session_state['periodicity'] = st.session_state['new_periodicity']

            st.selectbox(
                label="**Periodicity** - (Weekly/Monthly/Quarterly)",
                options=chart_mode_types,
                index=chart_mode_types.index(st.session_state['periodicity']),
                key="new_periodicity",
                on_change=chart_mode_idx_callback,
            )
        # with col2:
        #     agg_mode_types = ["Average per Store", "Sum of Stores"]

        #     if "agg_method" not in st.session_state:
        #         st.session_state['agg_method'] = agg_mode_types[0]

        #     def agg_method_idx_callback():
        #         st.session_state['agg_method'] = st.session_state['new_agg_method']

        #     st.selectbox(
        #         label="**Benchmark Aggregation Mode** - (Average per Store/Sum of Stores)", 
        #         options=agg_mode_types,
        #         index=agg_mode_types.index(st.session_state['agg_method']),
        #         key="new_agg_method",
        #         on_change=agg_method_idx_callback,
        #         disabled=True
        #     )

    # ----------------------------------------------- Horizontal View Selector ----------------------------------------------- #
    view_option_list = ["Target Store", "Target Store vs Benchmark Group", "Benchmark Group"]

    if "default_option_menu_idx" not in st.session_state:
        st.session_state["default_option_menu_idx"] = 1

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
        styles={"container": {"max-width": "None !important"}}
    )
    
    # with st.expander(label="Unfiltered/Unsliced Dataframe", expanded=False):
    #     st.dataframe(df_benchmark_stores)


    def spawn_charts(df, st_ss_periodicity=st.session_state['periodicity']):
        bcdc = BasketsChartDataframeCreator(df_benchmark_stores)
        df_input = bcdc.make_basket_chart_input_df(df, st_ss_periodicity)
        
        charts = ChartMaker()

        st_ss_periodicity = st.session_state['periodicity']

        metric_dict = {
            'store_baskets': 'Avg Total Baskets',
            'store_avg_basket_size': 'Avg Basket Size',
            'store_avg_basket_value': 'Avg Basket Value'
        }

        def spawn_yoy_charts():
            for metric, metric_renamed in metric_dict.items():
                st.plotly_chart(
                    charts.make_barchart_yoy(df_input, metric, metric_renamed, st_ss_periodicity).format_barchart_yoy(), 
                    use_container_width=True
                )

        def spawn_timeseries_charts():
            for metric, metric_renamed in metric_dict.items():
                st.plotly_chart(
                    charts.make_barchart_timeseries(df_input, metric, metric_renamed, st_ss_periodicity).format_barchart_timeseries(), 
                    use_container_width=True
                )
            
        if 'YoY' in st_ss_periodicity:
            spawn_yoy_charts()
        else:
            spawn_timeseries_charts()

    if view_option == "Target Store":
        spawn_charts(df_target_store)
    elif view_option == "Target Store vs Benchmark Group":
        col1, col2 = st.columns(2)
        with col1:
            spawn_charts(df_target_store)
        with col2:
            spawn_charts(df_benchmark_stores)
    elif view_option == "Benchmark Group":
        spawn_charts(df_benchmark_stores)

    
    st.write(datetime.now() - t0)
