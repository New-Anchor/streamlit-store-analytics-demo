import pandas as pd
import sqlalchemy
import streamlit as st


def render_page():

    st.header("SQL GUI")

    st.markdown("")

    col1, col2, col3 = st.columns(3)

    with col1:
        def clear_click_state():
            del st.session_state['click']
        st.selectbox(
            label="**Item Number/Subrange**",
            options=["Item Number", "Subrange"],
            index=0,
            # horizontal=True,
            key="item_or_subrange",
            on_change=clear_click_state
        )
    with col2:
        st.text_input(
            label="**Enter Item Number/Subrange**",
            key="text_input",
            help="If multiple values, use comma to separate them e.g. 5, 8, 13, 21 - using spaces is optional."
        )         
    with col3:
        st.number_input(
            label="**Case Claim Amount ($)**",
            value=0.00,
            key="claim_amount"
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        start_dt = st.date_input(label="**Start Date**") 
    with col2:
        end_dt = st.date_input(label="**End Date**")
    with col3:
        st.radio(
            label="**Product Basket**",
            options=["Type_1", "Type_2", "Type_3"],
            horizontal=True,
            key="basket_type"
        )

    try:
        if st.session_state["item_or_subrange"] == "Item Number":
            product_cd_list = st.session_state['text_input']
            product_cd_list = ','.join([f"'{str(int(i)).zfill(6)}'" for i in product_cd_list.split(',')])
            item_subr_filter = f"product_cd IN ({product_cd_list})"

            print(st.session_state['text_input'].split(','))
            print(product_cd_list)
            print(item_subr_filter)
        else:
            sub_range_cd_list = st.session_state['text_input']
            sub_range_cd_list = ','.join([f"'{str(int(i)).zfill(5)}'" for i in sub_range_cd_list.split(',')])
            item_subr_filter = f"sub_range_cd IN ({sub_range_cd_list})"
            print(item_subr_filter)

        if st.session_state["basket_type"] == "Type_1":
            basket_type = "('SMALL', 'MEDIUM', 'LARGE')"
        elif st.session_state["basket_type"] == "Type_2":
            basket_type = "('MEDIUM', 'LARGE')"
        else:
            basket_type = "('LARGE')"

        query = \
            f"""
            SELECT state_cd,
                   product_cd,
                   product_desc,
                   sub_range_cd,
                   SUM(nett_cases) AS total_cases
            FROM schema_x.table_1 AS r
            INNER JOIN schema_y.table_date AS d
                    ON r.date_id = d.date_id
            WHERE promo_price_ind = 'N'
              AND d.fisc_date BETWEEN '{start_dt}' AND '{end_dt}'
              AND {item_subr_filter}
              AND address_id IN (
                  SELECT DISTINCT address_id
                  FROM schema_z.table_store
                  WHERE product_basket IN {basket_type}
                    AND (store_channel_cd LIKE '%SOME_STRING_A%' OR store_channel_cd LIKE '%SOME_STRING_B%')
                    AND store_channel_cd NOT IN ('-', 'Name_0', 'Name_1', 'Name_2', 'Name_3', 'Other')
                    AND recent_store_nm NOT LIKE '%DO NOT USE%'
              )
            GROUP BY state_cd,
                     product_cd,
                     product_desc,
                     sub_range_cd
            """
        with st.expander(label="_View Query_", expanded=True):
            st.code(query, language="sql")
    except:
        st.warning("No Item Number or Subrange detected. You can enter multiple integers. Use comma to separate them.")

    # def init_conn():
    #     db_uri = sqlalchemy.engine.URL.create(
    #         drivername = 'REDACTED',
    #         username = 'REDACTED',
    #         password = 'REDACTED',
    #         host = 'REDACTED',
    #         port = 'REDACTED',
    #         database = 'REDACTED'
    #     )
    #     return sqlalchemy.create_engine(db_uri)

    # conn = init_conn()

    # @st.cache_data(show_spinner="Fetching data, please wait...")
    # def load_data():
    #     data = pd.read_sql(sqlalchemy.text(query), con=conn)
    #     return data

    # --------------------------- Fetch Query Button --------------------------- #

    if 'click' not in st.session_state:
        st.session_state['click'] = False

    def callback_btn():
        st.cache_data.clear()
        st.session_state['click'] = True
        st.session_state['dataframe'] = load_data()

    st.button("**Fetch Data**", on_click=callback_btn, disabled=True, use_container_width=True)

    # if st.session_state['click'] is True:
    #     data = st.session_state['dataframe']
    #     groupby_options = ["Item Number", "Subrange"]
    #     groupby_method = st.radio(
    #         label="**Group By**:", 
    #         options=groupby_options, 
    #         index=groupby_options.index(st.session_state["item_or_subrange"]),
    #         horizontal=True
    #     )
    #     if groupby_method == "SKU":
    #         data = data.groupby(['administration_state_cd', 'product_cd', 'product_desc'])['total_cases'].sum().reset_index()
    #     elif groupby_method == "Subrange":
    #         data = data.groupby(['administration_state_cd', 'sub_range_cd'])['total_cases'].sum().reset_index()
    #     data['claim_amount'] = st.session_state['claim_amount']
    #     data['total_claim'] = data['total_cases'] * data['claim_amount']

    #     st.dataframe(data, hide_index=True, use_container_width=True)
    #     st.markdown(f"Total Claim Amount: **${round(data['total_claim'].sum(), 2):,.2f}**")

    #     st.download_button(
    #         label="Download Table", 
    #         data=data.to_csv(index=False),
    #         file_name=f"back_claims_download.csv"
    #     )


