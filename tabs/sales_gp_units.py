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

    datasource = r"data/sales_gp_units_weekly.parquet"
    
    columns = ['address_id', 'finance_department_nm', 'promotion_ind',
               'warehouse', 'sales_qty', 'sales_ex_gst', 'gp_ex_gst', 
               'prom_wk_end_dt', 'prom_year_wk_num', 'prom_mth_num', 
               'prom_month_nm', 'prom_year_num', 'lped_qtr_nm', 'lped_year_num']
    
    address_filter = [('address_id', 'in', address_list)]
    
    @st.cache_data
    def load_sales_gp_units_data(data, columns, address_filter):
        return pd.read_parquet(data, columns=columns, filters=address_filter)

    # ---------------------------- Initialize Dataframes ---------------------------- #
    data = load_sales_gp_units_data(datasource, columns, address_filter)
    data['prom_mth_yr_dt'] = pd.to_datetime(data['prom_mth_num'].astype(str) + data['prom_year_num'].astype(str), format='%m%Y')
    data['lped_qtr_yr_dt'] = data['lped_qtr_nm'].str[:2] + '-' + data['lped_year_num'].astype(str)
    
    df_target_store = data[data['address_id'] == st.session_state['target_address_id']]
    df_benchmark_stores = data[data['address_id'].isin(st.session_state['benchmark_address_ids'])]

    # ------------------------------ Page Top ------------------------------ #
    st.header("**Sales/GP/Units** 📈")

    # ------------------------------ Filters ------------------------------ #
    with st.expander(label="**Settings**", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            chart_mode_types = ["YoY - Quarterly", 
                                "YoY - Monthly", 
                                "YoY - Weekly", 
                                "Quarterly", 
                                "Monthly", 
                                "Weekly"]

            if "periodicity" not in st.session_state:
                st.session_state['periodicity'] = chart_mode_types[-1]

            def chart_mode_idx_callback():
                st.session_state['periodicity'] = st.session_state['new_periodicity']

            st.selectbox(
                label="**Periodicity**",
                help="_**N.B.** - First LPED Quarter is REMOVED in YoY Quarterly (LPED). The reason is because it's not a full quarter and it is part of the PREVIOUS year's LPED quarter._",
                options=chart_mode_types,
                index=chart_mode_types.index(st.session_state['periodicity']),
                key="new_periodicity",
                on_change=chart_mode_idx_callback,
            )
        with col2:
            promo_status_types = ["Promo & Non-Promo", "Non-Promo Only", "Promo Only"]

            if "promotion_ind" not in st.session_state:
                st.session_state['promotion_ind'] = promo_status_types[0]

            def promo_selection_idx_callback():
                st.session_state['promotion_ind'] = st.session_state['new_promotion_ind']

            st.selectbox(
                label="**Promotion Status**",
                help="_Filter for promo/non-promo/all sales._",
                options=promo_status_types, 
                index=promo_status_types.index(st.session_state['promotion_ind']),
                key="new_promotion_ind",
                on_change=promo_selection_idx_callback,
            )
        with col3:
            agg_mode_types = ["Average per Store", "Sum of Stores"]

            if "agg_method" not in st.session_state:
                st.session_state['agg_method'] = agg_mode_types[0]

            def agg_method_idx_callback():
                st.session_state['agg_method'] = st.session_state['new_agg_method']

            st.selectbox(
                label="**Benchmark Aggregation Mode**",
                help="_Choose to see Benchmark Group as Total or Average per Store._",
                options=agg_mode_types,
                index=agg_mode_types.index(st.session_state['agg_method']),
                key="new_agg_method",
                on_change=agg_method_idx_callback,
            )
        
        if st.session_state['promotion_ind'] == "Non-Promo Only":
            df_target_store = df_target_store[df_target_store['promotion_ind'] == "N"]
            df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['promotion_ind'] == "N"]
        elif st.session_state['promotion_ind'] == "Promo Only":
            df_target_store = df_target_store[df_target_store['promotion_ind'] == "Y"]
            df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['promotion_ind'] == "Y"]

        col1, col2, col3 = st.columns(3)
        with col1:
            measure_types = ["Sales ex GST", "Gross Profit ex GST", "Units"]

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
            sales_types = ["All Scan Sales", "Warehouse", "3rd Party Suppliers"]

            if "sales_type" not in st.session_state:
                st.session_state['sales_type'] = sales_types[0]
            
            def sales_type_callback():
                st.session_state['sales_type'] = st.session_state['new_sales_type']
                del st.session_state['dept_filter']

            st.selectbox(
                label="**Sales Type**",
                help="_Choose between Metcash Warehouse and Directs & 3rd Party (product_cd prefixed with 'S')._",
                options=sales_types,
                index=sales_types.index(st.session_state['sales_type']),
                key="new_sales_type",
                on_change=sales_type_callback,
            )
        with col3:
            category_types = ["All Categories", "Core Sales", "Fresh", "Tobacco & Liquor", "Custom"]

            if "category_type" not in st.session_state:
                st.session_state['category_type'] = category_types[0]
            
            def category_callback():
                st.session_state['category_type'] = st.session_state['new_category_type']
                del st.session_state['dept_filter']

            st.selectbox(
                label="**Category**",
                help="_Auto changes to Custom when Finance Department modified._",
                options=category_types,
                index=category_types.index(st.session_state['category_type']),
                key="new_category_type",
                on_change=category_callback,
            )

        if st.session_state['sales_type'] == "Warehouse":
            df_target_store = df_target_store[df_target_store['warehouse'] == 'Y']
            df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['warehouse'] == 'Y']
        elif st.session_state['sales_type'] == "Other Suppliers":
            df_target_store = df_target_store[df_target_store['warehouse'] == 'N']
            df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['warehouse'] == 'N']

        if st.session_state['category_type'] != "Custom":
            if st.session_state['category_type'] == "Core Sales":
                df_target_store = df_target_store[df_target_store['finance_department_nm'].isin(['GROCERY', 'DAIRY', 'FROZEN', 'VARIETY'])]
                df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['finance_department_nm'].isin(['GROCERY', 'DAIRY', 'FROZEN', 'VARIETY'])]
            elif st.session_state['category_type'] == "Fresh":
                df_target_store = df_target_store[df_target_store['finance_department_nm'].isin(['BAKERY', 'DELI', 'FRUIT & VEG', 'MEAT', 'OTHER', 'SEAFOOD'])]
                df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['finance_department_nm'].isin(['BAKERY', 'DELI', 'FRUIT & VEG', 'MEAT', 'OTHER', 'SEAFOOD'])]
            elif st.session_state['category_type'] == "Tobacco & Liquor":
                df_target_store = df_target_store[df_target_store['finance_department_nm'].isin(['TOBACCO', 'LIQUOR'])]
                df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['finance_department_nm'].isin(['TOBACCO', 'LIQUOR'])]

        dept_filter_options = df_benchmark_stores['finance_department_nm'].unique().tolist()

        if 'dept_filter' not in st.session_state:
            st.session_state['dept_filter'] = dept_filter_options

        # # Debugging session states
        # col1, col2 = st.columns(2)
        # with col1:
        #     st.write(df_benchmark_stores['finance_department_nm'].unique().tolist())
        # with col2:
        #     st.write(st.session_state['dept_filter'])

        def callback_dept_filter():
            st.session_state['dept_filter'] = st.session_state['new_dept_filter']
            st.session_state['category_type'] = "Custom"

        st.multiselect(
            label="**Department Filter**",
            options=df_benchmark_stores['finance_department_nm'].unique().tolist(),
            default=st.session_state['dept_filter'],
            key="new_dept_filter",
            on_change=callback_dept_filter
        )

        # if len(st.session_state['dept_filter']) > 0:
        df_target_store = df_target_store[df_target_store['finance_department_nm'].isin(st.session_state['dept_filter'])]
        df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['finance_department_nm'].isin(st.session_state['dept_filter'])]

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
        styles={
            "container": {
                "max-width": "None !important",
                "font-size": "15px"
            }
        }
    )
    
    # with st.expander(label="Unfiltered/Unsliced Dataframe", expanded=False):
    #     st.dataframe(data)

    def spawn_charts(
        df,
        measure = st.session_state['measure_type'],
        st_ss_periodicity = st.session_state['periodicity'],
        st_ss_agg_method = st.session_state['agg_method']
    ):
        measure_dict = {
            'Sales ex GST': 'sales_ex_gst',
            'Gross Profit ex GST': 'gp_ex_gst',
            'Units': 'sales_qty'
        }
        metric = measure_dict[measure]
        metric_renamed = measure

        scdc = SalesChartDataframeCreator(df_benchmark_stores)
        df_input = scdc.make_sales_chart_input_df(df, metric, st_ss_periodicity, st_ss_agg_method)

        if st_ss_periodicity == 'YoY - Quarterly':
            df_input = df_input.iloc[1:]

        charts = ChartMaker()
        
        def spawn_yoy_charts():
            st.plotly_chart(
                charts.make_barchart_yoy(df_input, metric, metric_renamed, st_ss_periodicity).format_barchart_yoy(), 
                use_container_width=True
            )
            if measure == 'Gross Profit ex GST':
                st.plotly_chart(
                    charts.make_ratio_linechart_yoy(df_input, metric, metric_renamed, st_ss_periodicity).format_ratio_linechart_yoy(), 
                    use_container_width=True
                )
            st.plotly_chart(
                charts.make_ratio_linechart_yoy(df_input, metric, metric_renamed, st_ss_periodicity, 'warehouse').format_ratio_linechart_yoy(), 
                use_container_width=True
            )
            st.plotly_chart(
                charts.make_ratio_linechart_yoy(df_input, metric, metric_renamed, st_ss_periodicity, 'promotion_ind').format_ratio_linechart_yoy(), 
                use_container_width=True
            )

        def spawn_timeseries_charts():
            st.plotly_chart(
                charts.make_barchart_timeseries(df_input, metric, metric_renamed, st_ss_periodicity).format_barchart_timeseries(), 
                use_container_width=True
            )
            if measure == 'Gross Profit ex GST':
                st.plotly_chart(
                    charts.make_linechart_timeseries(df_input, metric, metric_renamed, st_ss_periodicity, indicator='gp_pct').fig, 
                    use_container_width=True
                )
            st.plotly_chart(
                charts.make_linechart_timeseries(df_input, metric, metric_renamed, st_ss_periodicity, indicator='warehouse').fig, 
                use_container_width=True
            )
            st.plotly_chart(
                charts.make_linechart_timeseries(df_input, metric, metric_renamed, st_ss_periodicity, indicator='promotion_ind').fig, 
                use_container_width=True
            )

        if 'YoY' in st_ss_periodicity:
            spawn_yoy_charts()
        else:
            spawn_timeseries_charts()
        
        # with st.expander(label="View/Download Data", expanded=False):
        #     st.dataframe(df_input, use_container_width=True)

    if len(st.session_state['dept_filter']) > 0:
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
