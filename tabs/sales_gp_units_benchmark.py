import pandas as pd
import streamlit as st
from charts.indexed_charts import create_df_indexed_metric, indexed_comps_chart
from charts.bubble_charts import store_bubble_chart
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
    @st.cache_data(show_spinner=False)
    def load_store_attributes():
        df_store_attrs = pd.read_parquet(r'data/store_attributes_weekly.parquet')
        df_store_attrs = df_store_attrs.sort_values('prom_wk_end_dt', ascending=False)
        df_store_attrs = df_store_attrs.drop_duplicates('address_id', keep='first')
        return df_store_attrs
    
    df_stores = load_store_attributes()

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
    data['prom_wk_end_dt'] = pd.to_datetime(data['prom_wk_end_dt']).dt.date
    min_dt = min(data['prom_wk_end_dt'])
    max_dt = max(data['prom_wk_end_dt'])

    if 'start_dt' not in st.session_state:
        st.session_state['start_dt'] = min_dt
    if 'end_dt' not in st.session_state:
        st.session_state['end_dt'] = max_dt
    
    df_target_store = data[data['address_id'] == st.session_state['target_address_id']]
    df_benchmark_stores = data[data['address_id'].isin(st.session_state['benchmark_address_ids'])]

    # ------------------------------ Page Top ------------------------------ #
    st.header("**Benchmark - Sales, GP & Units** ⚖️")

    # ------------------------------ Filters ------------------------------ #
    with st.expander(label="**Settings**", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox(
                label="**Periodicity**",
                help="_Benchmarked only for Weekly_",
                options=["Weekly"],
                key="benchmark_periodicity",
                disabled=True
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
                help="_Average per Store = Unweighted Average, Sum of Stores = Weighted Average_",
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
                help="_Choose between Warehouse or External Suppliers._",
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
        elif st.session_state['sales_type'] == "Customer Directs":
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

        df_target_store = df_target_store[df_target_store['prom_wk_end_dt'].between(st.session_state['start_dt'], st.session_state['end_dt'])]
        df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['prom_wk_end_dt'].between(st.session_state['start_dt'], st.session_state['end_dt'])]

    # ------------------------ Benchmark Date Range ------------------------ #
    col1, col2 = st.columns(2)
    with col1:
        def start_dt_callback():
            st.session_state['start_dt'] = st.session_state['new_start_dt']
        st.date_input(
            label="**Benchmark Start Date**",
            help="_**N.B.** - Choose the appropriate Tuesday (prom week end date) with regards to the Implementation Date_",
            value=st.session_state['start_dt'],
            min_value=min_dt,
            max_value=max_dt,
            key='new_start_dt',
            on_change=start_dt_callback
        )
    with col2:
        def end_dt_callback():
            st.session_state['end_dt'] = st.session_state['new_end_dt']
        st.date_input(
            label="**Benchmark End Date**",
            help="_**N.B.** - Choose the appropriate Tuesday (prom week end date) with regards to the Implementation Date_",
            value=st.session_state['end_dt'],
            min_value=min_dt,
            max_value=max_dt,
            key='new_end_dt',
            on_change=end_dt_callback
        )

    # with st.expander(label="Filtered Input Dataframes", expanded=True):
        # st.dataframe(df_target_store, use_container_width=True)
        # st.dataframe(df_benchmark_stores, use_container_width=True)

    def spawn_charts(measure=st.session_state['measure_type'], st_ss_agg_method=st.session_state['agg_method']):
        measure_dict = {
            'Sales ex GST': 'sales_ex_gst',
            'Gross Profit ex GST': 'gp_ex_gst',
            'Units': 'sales_qty'
        }
        metric = measure_dict[measure]
        metric_renamed = measure

        df_store_sales_idx = create_df_indexed_metric(df_target_store, metric, metric_renamed, st_ss_agg_method)
        df_benchmark_sales_idx = create_df_indexed_metric(df_benchmark_stores, metric, metric_renamed, st_ss_agg_method)
        
        # Make benchmark indexed chart
        st.plotly_chart(indexed_comps_chart(df_store_sales_idx, df_benchmark_sales_idx), use_container_width=True)

        # This is the cumulative sum version of the dataframes indexed on first wk_start_dt
        df_store_sales_idx_cumsum = create_df_indexed_metric(df_target_store, metric, metric_renamed, st_ss_agg_method, cumsum=True)    
        df_benchmark_sales_idx_cumsum = create_df_indexed_metric(df_benchmark_stores, metric, metric_renamed, st_ss_agg_method, cumsum=True)

        # Make benchmark cumulative indexed chart
        st.plotly_chart(indexed_comps_chart(df_store_sales_idx_cumsum, df_benchmark_sales_idx_cumsum), use_container_width=True)

        # Make Sales per sqm bubble chart
        st.plotly_chart(store_bubble_chart(df_target_store, df_benchmark_stores, df_stores, metric, metric_renamed), use_container_width=True)
        
        # with st.expander(label="View/Download Data", expanded=False):
        #     st.dataframe(df_input, use_container_width=True)
        #     st.download_button(
        #         label="Download Table", 
        #         data=make_csv(df_input),
        #         file_name="ChartTable.csv"
        #     )
    try:
        spawn_charts()
    except IndexError:
        st.error("You must select at least ONE Department Filter")


    st.write(datetime.now() - t0)
