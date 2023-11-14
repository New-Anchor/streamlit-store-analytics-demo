import pandas as pd
import plotly.express as px
import streamlit as st
import sqlalchemy
from datetime import datetime, timedelta
from sql_queries import redshift_queries


today_dt = datetime.now()
year_ago_dt = today_dt - timedelta(days = 365)
min_dt = today_dt - timedelta(days = 999)


# def init_conn():
#     db_uri = sqlalchemy.engine.URL.create(
#         drivername = 'postgresql+psycopg2',
#         username = '### REDACTE D###',
#         password = '### REDACTED ###',
#         host = '### REDACTED ###',
#         port = '### REDACTED ###',
#         database = '### REDACTED ###',
#     )
#     return sqlalchemy.create_engine(db_uri)

# conn = init_conn()


def render_page():
    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            background-color: #2979bf;
            border-color: #FFFFFF;
            color: #FFFFFF;
        }
        div.stButton > button:hover {
            background-color: #2979bf;
            border-color: #00008B;
            color: #FFFFFF;
        }
        div.stButton > button:focus {
            background-color: #EEEEEE;
            border-color: #EEEEEE;
        }
        div.stDownloadButton > button {
            background-color: #2979bf;
            border-color: #2979bf;
            color: #EEEEEE;
        }
        div.stDownloadButton > button:hover {
            background-color: #E43424;
            border-color: #00008B;
            color: #FFFFFF;
        }
        div.stDownloadButton > button:focus {
            background-color: #EEEEEE;
            border-color: #EEEEEE;
        }
        div[data-testid="stExpander"] div[role="button"] p {
            font-size: 13px;
            font-weight: 500; 
        }
        </style>
        """, unsafe_allow_html=True
    )


    @st.cache_data(show_spinner="Fetching data, please wait...")
    def load_data(query_type, address_id, start_date, end_date, periodicity):
        if query_type == 'Scan Sales':
            sql_query = redshift_queries.scan_sales_query(address_id, start_date, end_date)
        elif query_type == 'Unique Items':
            sql_query = redshift_queries.unique_products_query(address_id, start_date, end_date, periodicity)
        data = pd.read_sql(sqlalchemy.text(sql_query), con=conn)
        return data

    # -------- Top of page -------- #
    st.header("**Redshift Interface** 🖥️")
    st.markdown('---')
    st.sidebar.markdown(
        f"""
        ---
        
        **Target Store:**

        {st.session_state['store_nm_selected']} ({st.session_state['target_store_state']})
        
        {st.session_state['target_store_chanzfp']}

        ---
        **No. of Benchmark Stores:** 
        
        {len(st.session_state['benchmark_address_ids'])}
        """
    )

    col1, col2, col3 = st.columns([1, 1, 4.4])
    with col1:
        start_date = st.date_input(
            label="**Start Date**",
            help="Select the appropriate prom_wk_end_dt (Tuesday)",
            value=year_ago_dt,
            min_value=min_dt,
            max_value=today_dt,
            # key='new_start_dt',
            # on_change=start_dt_callback
        )

    with col2:
        end_date = st.date_input(
            label='**End Date**',
            help="Select the appropriate prom_wk_end_dt (Tuesday)",
            value=today_dt,
            min_value=min_dt,
            max_value=today_dt,
            # key='new_start_dt',
            # on_change=start_dt_callback
        )

    with col3:
        options = ['Scan Sales', 'Unique Items']
        if 'query_type' not in st.session_state:
            st.session_state['query_type'] = options[0]
        
        def callback_query_type():
            st.session_state['query_type'] = st.session_state['new_query_type']
        
        st.session_state['query_type'] = st.selectbox(
            label='**Query Type**',
            options=options, 
            index=options.index(st.session_state['query_type']),
            key='new_query_type',
            on_change=callback_query_type,
            # disabled=True
        )
    
    if st.session_state['query_type'] == 'Unique Items':
        query_period_types = ("Weekly", "Monthly")
        if "query_periodicity" not in st.session_state:
            st.session_state["query_periodicity"] = query_period_types[0]

        def callback_query_period_type():
            st.session_state["query_periodicity"] = st.session_state["new_query_periodicity"]
        
        st.radio(
            label=" ",
            options=query_period_types,
            index=query_period_types.index(st.session_state["query_periodicity"]),
            label_visibility="collapsed",
            key="new_query_periodicity",
            on_change=callback_query_period_type
        )    
    
    # --------------------------- Fetch Query Button --------------------------- #
    if 'click' not in st.session_state:
        st.session_state['click'] = False

    def callback_btn():
        st.session_state['click'] = True
        st.session_state['dataframe'] = load_data(
            st.session_state['query_type'], 
            st.session_state['target_address_id'],
            start_date, end_date, st.session_state['query_periodicity']
        )
    
    st.button("**Fetch Data**", on_click=callback_btn, use_container_width=True, disabled=True)

    # --------------------------- Display Query ---------------------- #
    if st.session_state['query_type'] == 'Scan Sales':
        sql_query = redshift_queries.scan_sales_query(st.session_state['target_address_id'], start_date, end_date)
    elif st.session_state['query_type'] == 'Unique Items':
        sql_query = redshift_queries.unique_products_query(st.session_state['target_address_id'], start_date, end_date, st.session_state['query_periodicity'])
    st.code(sql_query, language="sql")

    # --------------------------- If Unique Items is Selected --------------------------- #
    if st.session_state['query_type'] == 'Unique Items':
        if st.session_state['click'] is True:
            data = st.session_state['dataframe']
            if st.session_state['query_periodicity'] == 'Monthly':
                data['time_period'] = pd.to_datetime(data['prom_month_nm'] + '-' + data['prom_year_num'].astype(str), format="%B-%Y")
                data = data.sort_values(['promotion_ind', 'time_period'], ascending=True)
            elif st.session_state['query_periodicity'] == 'Weekly':
                data = data.rename(columns={'prom_wk_end_dt': 'time_period'})
                data = data.sort_values(['promotion_ind', 'time_period'], ascending=True)
            df = data[data['promotion_ind'] == 'N']

            st.plotly_chart(px.bar(df, x='time_period', y='count', title='Unique Items'), use_container_width=True)

            st.download_button(
                label="Download Data", 
                data=df.to_csv(index=False),
                file_name=f"{st.session_state['store_nm_selected']} Unique Items ({start_date} to {end_date}).csv"
            )

    # --------------------------- If Scan Sales is Selected --------------------------- #
    if st.session_state['query_type'] == 'Scan Sales':
        if st.session_state['click'] is True:
            st.checkbox(
                label="Include Direct & 3rd Party Products",
                value=False,
                key="checkbox"
            )
            data = st.session_state['dataframe']
            data = data.astype({
                'product_cd': str,
                'product_desc': str,
                'promotion_ind': str,
                'sales_qty': float,
                'sales_ex_gst': float,
                'gp_ex_gst': float,
                'total_days': int,
                'avg_sell_ex_gst': float,
                'sales_qty_per_day': float,
                'finance_department_nm': str,
                'msc_dept_nm': str,
                'msc_category_nm': str,
                'msc_commodity_nm': str
            })
            if st.session_state['checkbox'] is False:
                data = data[~data['product_cd'].str.contains('S')]
            
            with st.expander("**View Output Table:**", expanded=False):
                st.dataframe(data, height=600, use_container_width=True)

            st.download_button(
                label="Download Table", 
                data=data.to_csv(index=False),
                file_name=f"{st.session_state['store_nm_selected']} Scan Sales ({start_date} to {end_date}).csv"
            )

            st.markdown('---')
            st.markdown(f"### Summary Statistics - {st.session_state['store_nm_selected']}  ({start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')})")
            st.write("")

            with st.expander(label="**Sales, Gross Profit, and Unique Product Count**", expanded=True):

                col1, col2, col3 = st.columns(3)

                total_sales = round(data['sales_ex_gst'].sum(), 2)
                total_gp = round(data['gp_ex_gst'].sum(), 2)
                total_gp_pct = round(data['gp_ex_gst'].sum() / data['sales_ex_gst'].sum() * 100, 2)
                total_item_count = len(data['product_cd'].unique())

                with col1:
                    st.markdown("##### Store Total")
                    st.markdown(f"**Total Sales ex GST:** &nbsp;&nbsp;&nbsp;&nbsp; ${total_sales:,}")
                    st.markdown(f"**Total Gross Profit ex GST:** &nbsp;&nbsp;&nbsp;&nbsp; ${total_gp:,}")
                    st.markdown(f"**Wt. Avg. Gross Profit Margin:** &nbsp;&nbsp;&nbsp;&nbsp; {total_gp_pct}%")
                    st.markdown(f"**Total Unique Products:** &nbsp;&nbsp;&nbsp;&nbsp; {total_item_count:,}")

                np_sales = round(data[data['promotion_ind']=='N']['sales_ex_gst'].sum(), 2)
                np_sales_pct_total = round(np_sales / total_sales * 100, 2)
                np_gp = round(data[data['promotion_ind']=='N']['gp_ex_gst'].sum(), 2)
                np_gp_pct_total = round(np_gp / total_gp * 100, 2)
                np_gp_pct = round(data[data['promotion_ind']=='N']['gp_ex_gst'].sum() / data[data['promotion_ind']=='N']['sales_ex_gst'].sum() * 100, 2) 
                np_item_count = len(data[data['promotion_ind']=='N']['product_cd'].unique())

                with col2:
                    st.markdown("##### Non-Promotional")
                    st.markdown(f"**Sales ex GST (Non-promo):** &nbsp;&nbsp;&nbsp;&nbsp; ${np_sales:,} - ({np_sales_pct_total}% of Total Sales)")
                    st.markdown(f"**Gross Profit ex GST (Non-promo):** &nbsp;&nbsp;&nbsp;&nbsp; ${np_gp:,} - ({np_gp_pct_total}% of Total GP)")
                    st.markdown(f"**Wt. Avg. Gross Profit Margin (Non-promo):** &nbsp;&nbsp;&nbsp;&nbsp; {np_gp_pct}%")
                    st.markdown(f"**Unique Products (Non-promo):** &nbsp;&nbsp;&nbsp;&nbsp; {np_item_count:,}")

                promo_sales = round(data[data['promotion_ind']=='Y']['sales_ex_gst'].sum(), 2)
                promo_sales_pct_total = round(promo_sales / total_sales * 100, 2)
                promo_gp = round(data[data['promotion_ind']=='Y']['gp_ex_gst'].sum(), 2)
                promo_gp_pct_total = round(promo_gp / total_gp * 100, 2) 
                promo_gp_pct = round(data[data['promotion_ind']=='Y']['gp_ex_gst'].sum() / data[data['promotion_ind']=='Y']['sales_ex_gst'].sum() * 100, 2)
                promo_item_count = len(data[data['promotion_ind']=='Y']['product_cd'].unique())

                with col3:
                    st.markdown("##### Promotional")
                    st.markdown(f"**Sales ex GST (Promo):** &nbsp;&nbsp;&nbsp;&nbsp; ${promo_sales:,} - ({promo_sales_pct_total}% of Total Sales)")
                    st.markdown(f"**Gross Profit ex GST (Promo):** &nbsp;&nbsp;&nbsp;&nbsp; ${promo_gp:,} - ({promo_gp_pct_total}% of Total GP)")
                    st.markdown(f"**Wt. Avg. Gross Profit Margin (Promo):** &nbsp;&nbsp;&nbsp;&nbsp; {promo_gp_pct}%")
                    st.markdown(f"**Unique Products (Promo):** &nbsp;&nbsp;&nbsp;&nbsp; {promo_item_count:,}")

                # ------------------------------------------------------ If Directs & 3rd Party Checkbox is Selected ------------------------------------------------------ #
                if st.session_state['checkbox'] is True:
                    st.markdown(f"#### _Directs & 3rd Party_")
                    st.write("")

                    df_s_code = data[data['product_cd'].str.contains('S')]

                    col1, col2, col3 = st.columns(3)

                    total_s_code_sales = round(df_s_code['sales_ex_gst'].sum(), 2)
                    s_code_sales_pct_total = round(total_s_code_sales / total_sales * 100, 2)
                    total_s_code_gp = round(df_s_code['gp_ex_gst'].sum(), 2)
                    s_code_gp_pct_total = round(total_s_code_gp / total_gp * 100, 2)
                    total_s_code_gp_pct = round(df_s_code['gp_ex_gst'].sum() / df_s_code['sales_ex_gst'].sum() * 100, 2)
                    s_code_item_count = len(df_s_code['product_cd'].unique())
                    s_code_item_pct_total = round(s_code_item_count / total_item_count * 100, 2)

                    with col1:
                        st.markdown("##### Directs & 3rd Party Total")
                        st.markdown(f"**Total Sales ex GST:** &nbsp;&nbsp;&nbsp;&nbsp; ${total_s_code_sales:,} - ({s_code_sales_pct_total}% of Store Total)")
                        st.markdown(f"**Total Gross Profit ex GST:** &nbsp;&nbsp;&nbsp;&nbsp; ${total_s_code_gp:,} - ({s_code_gp_pct_total}% of Total GP)")
                        st.markdown(f"**Wt. Avg. Gross Profit Margin:** &nbsp;&nbsp;&nbsp;&nbsp; {total_s_code_gp_pct}%")
                        st.markdown(f"**Total Unique Products:** &nbsp;&nbsp;&nbsp;&nbsp; {s_code_item_count:,} - ({s_code_item_pct_total}% of Total Unique Products)")

                    np_s_code_sales = round(df_s_code[df_s_code['promotion_ind']=='N']['sales_ex_gst'].sum(), 2)
                    np_s_code_sales_pct_total = round(np_s_code_sales / total_s_code_sales * 100, 2)
                    np_s_code_gp = round(df_s_code[df_s_code['promotion_ind']=='N']['gp_ex_gst'].sum(), 2)
                    np_s_code_gp_pct_total = round(np_s_code_gp / total_s_code_gp * 100, 2)
                    np_s_code_gp_pct = round(df_s_code[df_s_code['promotion_ind']=='N']['gp_ex_gst'].sum() / df_s_code[df_s_code['promotion_ind']=='N']['sales_ex_gst'].sum() * 100, 2) 
                    np_s_code_item_count = len(df_s_code[df_s_code['promotion_ind']=='N']['product_cd'].unique())

                    with col2:
                        st.markdown("##### Non-Promotional")
                        st.markdown(f"**Sales ex GST (Non-promo):** &nbsp;&nbsp;&nbsp;&nbsp; ${np_s_code_sales:,} - ({np_s_code_sales_pct_total}% of Directs & 3rd Party Sales)")
                        st.markdown(f"**Gross Profit ex GST (Non-promo):** &nbsp;&nbsp;&nbsp;&nbsp; ${np_s_code_gp:,} - ({np_s_code_gp_pct_total}% of Directs & 3rd Party GP)")
                        st.markdown(f"**Wt. Avg. Gross Profit Margin (Non-promo):** &nbsp;&nbsp;&nbsp;&nbsp; {np_s_code_gp_pct}%")
                        st.markdown(f"**Unique Products (Non-promo):** &nbsp;&nbsp;&nbsp;&nbsp; {np_s_code_item_count:,}")

                    promo_s_code_sales = round(df_s_code[df_s_code['promotion_ind']=='Y']['sales_ex_gst'].sum(), 2)
                    promo_s_code_sales_pct_total = round(promo_s_code_sales / total_s_code_sales * 100, 2)
                    promo_s_code_gp = round(df_s_code[df_s_code['promotion_ind']=='Y']['gp_ex_gst'].sum(), 2)
                    promo_s_code_gp_pct_total = round(promo_s_code_gp / total_s_code_gp * 100, 2)
                    promo_s_code_gp_pct = round(df_s_code[df_s_code['promotion_ind']=='Y']['gp_ex_gst'].sum() / df_s_code[df_s_code['promotion_ind']=='Y']['sales_ex_gst'].sum() * 100, 2)
                    promo_s_code_item_count = len(df_s_code[df_s_code['promotion_ind']=='Y']['product_cd'].unique())

                    with col3:
                        st.markdown("##### Promotional")
                        st.markdown(f"**Sales ex GST (Promo):** &nbsp;&nbsp;&nbsp;&nbsp; ${promo_s_code_sales:,} - ({promo_s_code_sales_pct_total}% of Directs & 3rd Party Sales)")
                        st.markdown(f"**Gross Profit ex GST (Promo):** &nbsp;&nbsp;&nbsp;&nbsp; ${promo_s_code_gp:,} - ({promo_s_code_gp_pct_total}% of Directs & 3rd Party GP)")
                        st.markdown(f"**Wt. Avg. Gross Profit Margin (Promo):** &nbsp;&nbsp;&nbsp;&nbsp; {promo_s_code_gp_pct}%")
                        st.markdown(f"**Unique Products (Promo):** &nbsp;&nbsp;&nbsp;&nbsp; {promo_s_code_item_count:,}")

            with st.expander(label="**Finance Department - Percentage of Total & wt. avg. GP%**", expanded=True):
                df_fin_dept = data.groupby(['finance_department_nm', 'promotion_ind']).agg({'sales_ex_gst': 'sum', 'gp_ex_gst': 'sum'})
                df_fin_dept['gp_pct'] = df_fin_dept['gp_ex_gst'] / df_fin_dept['sales_ex_gst']
                st.dataframe(df_fin_dept.sort_values('gp_ex_gst', ascending=False), use_container_width=True)

            with st.expander(label="**MSC Department - Percentage of Total & wt. avg. GP%**", expanded=True):
                df_msc_dept = data.groupby(['msc_dept_nm', 'promotion_ind']).agg({'sales_ex_gst': 'sum', 'gp_ex_gst': 'sum'})
                df_msc_dept['gp_pct'] = df_msc_dept['gp_ex_gst'] / df_msc_dept['sales_ex_gst']
                st.dataframe(df_msc_dept.sort_values('gp_ex_gst', ascending=False), use_container_width=True)
            
            with st.expander(label="**MSC Category - Percentage of Total & wt. avg. GP%**", expanded=True):
                df_msc_category = data.groupby(['msc_category_nm', 'promotion_ind']).agg({'sales_ex_gst': 'sum', 'gp_ex_gst': 'sum'})
                df_msc_category['gp_pct'] = df_msc_category['gp_ex_gst'] / df_msc_category['sales_ex_gst']
                st.dataframe(df_msc_category.sort_values('gp_ex_gst', ascending=False), use_container_width=True)

            with st.expander(label="**Price Elasticity of Demand - Midpoint Method**", expanded=True):
                df_np = data[['product_cd', 'product_desc', 'avg_sell_ex_gst', 'sales_qty_per_day']][data['promotion_ind'] == 'N'].rename(
                    columns={'avg_sell_ex_gst': 'avg_sell_np', 'sales_qty_per_day': 'sales_qty_np'}
                )
                df_promo = data[['product_cd', 'product_desc', 'avg_sell_ex_gst', 'sales_qty_per_day']][data['promotion_ind'] == 'Y'].rename(
                    columns={'avg_sell_ex_gst': 'avg_sell_promo', 'sales_qty_per_day': 'sales_qty_promo'}
                )
                df_elas = pd.merge(df_np, df_promo, how='inner', on=['product_cd', 'product_desc'])
                df_elas = df_elas[['product_cd', 'product_desc', 'sales_qty_np', 'sales_qty_promo', 'avg_sell_np', 'avg_sell_promo']]
                df_elas['pct_qty_change'] = (df_elas['sales_qty_np'] - df_elas['sales_qty_promo']) / ((df_elas['sales_qty_np'] + df_elas['sales_qty_promo']) / 2)
                df_elas['pct_sell_change'] = (df_elas['avg_sell_np'] - df_elas['avg_sell_promo']) / ((df_elas['avg_sell_np'] + df_elas['avg_sell_promo']) / 2)
                df_elas['Price Elasticity of Demand Estimate'] = round(df_elas['pct_qty_change'] / df_elas['pct_sell_change'], 2)
                data_elas = pd.merge(data, df_elas[['product_cd', 'Price Elasticity of Demand Estimate']], how='inner', on='product_cd')
                data_elas = data_elas[['product_cd', 'product_desc', 'promotion_ind', 'sales_qty', 'sales_ex_gst', 'gp_ex_gst', 'avg_sell_ex_gst', 'sales_qty_per_day', 
                                       'Price Elasticity of Demand Estimate', 'finance_department_nm', 'msc_dept_nm', 'msc_category_nm', 'msc_commodity_nm']]
                st.dataframe(data_elas, use_container_width=True)

            st.markdown("---")


    # st.write(st.session_state)

