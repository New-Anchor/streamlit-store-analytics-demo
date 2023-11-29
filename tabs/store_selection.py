import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder, AgGridTheme, DataReturnMode
from st_aggrid.shared import GridUpdateMode


def render_page():
    #Loading all data upon initialization
    @st.cache_data(show_spinner=False)
    def load_store_attributes():
        df_store_attrs = pd.read_parquet(r'data/store_attributes_weekly.parquet')
        df_store_attrs = df_store_attrs.sort_values('prom_wk_end_dt', ascending=False)
        df_store_attrs = df_store_attrs.drop_duplicates('address_id', keep='first')
        return df_store_attrs

    df_stores = load_store_attributes()

    # ------------------- Top of Page ------------------- #
    st.markdown("## **Store Selector 🛠️** ##")
    st.markdown(
        """
        Select the store you would like to review in the selection box below. The benchmark will be auto-generated using the selected store's
        **State**, **Channel** and **Zone**.
        """
    )

    selectbox_store_nm_list = df_stores['Store Name'].unique().tolist()
    selectbox_store_nm_list.insert(0, "")

    if 'store_nm_selected' not in st.session_state:
        st.session_state['store_nm_selected'] = ""

    def idx_callback():
        for key in st.session_state.keys():
            if key not in ['new_store_nm']:
                del st.session_state[key]
        st.session_state['store_nm_selected'] = st.session_state['new_store_nm']
        print(f"*** NEW STORE SELECTION: {st.session_state['new_store_nm']} ***")

    st.selectbox(
        label=f"**Select Store** - _({len(df_stores['Store Name'].unique())} total)_", 
        options=selectbox_store_nm_list, 
        index=selectbox_store_nm_list.index(st.session_state['store_nm_selected']),
        key='new_store_nm',
        on_change=idx_callback
        )
    
    if st.session_state['store_nm_selected'] != "":
        df_selected_store = df_stores[df_stores['Store Name'] == st.session_state['store_nm_selected']]
        target_store_info = df_selected_store.to_dict(orient='records')
        
        if 'target_address_id' not in st.session_state:
            st.session_state['target_address_id'] = target_store_info[0]['address_id']

        if 'target_store_state' not in st.session_state:
            st.session_state['target_store_state'] = target_store_info[0]['State']

        if 'target_store_chanzfp' not in st.session_state:
            st.session_state['target_store_chanzfp'] = target_store_info[0]['CHAN+ZFP']


        st.write(
            f"""
            Benchmark will be constructed using : 
            
            **State :**  {df_selected_store['State'].values[0]} &emsp;&emsp;&emsp;
            **Channel & Zone :** {df_selected_store['CHAN+ZFP'].values[0]}
            """
            )
        with st.expander(label='_View store details_', expanded=False):
            st.write(
                f"""
                **Store ID :** {target_store_info[0]['address_id']} &emsp;&emsp;&emsp;

                **Store Name :** {target_store_info[0]['Store Name']} &emsp;&emsp;&emsp;

                **State :** {target_store_info[0]['State']} &emsp;&emsp;&emsp;
                
                **Channel & Zone :** {target_store_info[0]['CHAN+ZFP']} &emsp;&emsp;&emsp;
                
                **Location :** {target_store_info[0]['store_address']} &emsp;&emsp;&emsp;
                
                **Store Owner :** {target_store_info[0]['Store Owner']} &emsp;&emsp;&emsp;
                
                **Store Size :** {target_store_info[0]['Store Size']}sqm
                
                **Subsidy Program 1 :** {target_store_info[0]['Subsidy Program 1']} &emsp;&emsp;&emsp;
                
                **Subsidy Program 2 :** {target_store_info[0]['Subsidy Program 2']} &emsp;&emsp;&emsp;
                """
            )
        st.write("---")

        st.markdown("### _Optional_ - Modify Benchmark Group")
        st.markdown(
            """
            Choose between: 
            * Default benchmark group - uses target store's State and CHAN+ZFP
            * Custom - by default everything is selected (i.e. National)
            """
        )
        
        benchmark_types = ("Default", "Custom")
        if "benchmark_type" not in st.session_state:
            st.session_state["benchmark_type"] = benchmark_types[0]

        def callback_benchmark_type():
            st.session_state["benchmark_type"] = st.session_state["new_benchmark_type"]
        
        st.radio(
            label=" ",
            options=benchmark_types,
            index=benchmark_types.index(st.session_state["benchmark_type"]),
            label_visibility="collapsed",
            key="new_benchmark_type",
            on_change=callback_benchmark_type
        )

        if st.session_state["benchmark_type"] == "Default":
            df_benchmark_stores = df_stores[
                (df_stores["State"] == target_store_info[0]["State"]) &
                (df_stores["CHAN+ZFP"] == target_store_info[0]["CHAN+ZFP"])
            ]

            col1, col2, = st.columns(2)

            with col1:
                if "benchmark_states" not in st.session_state:
                    st.session_state["benchmark_states"] = df_benchmark_stores["State"].unique().tolist()

                st.session_state["benchmark_states"] = st.multiselect(
                    label="**State**", 
                    options=df_benchmark_stores["State"].sort_values().unique().tolist(),
                    default=df_benchmark_stores["State"].unique().tolist(),
                    disabled=True
                    )
                
            df_benchmark_stores = df_benchmark_stores[df_benchmark_stores['State'].isin(st.session_state['benchmark_states'])]

            with col2:
                if "benchmark_chanzfp" not in st.session_state:
                    st.session_state["benchmark_chanzfp"] = df_benchmark_stores["CHAN+ZFP"].unique().tolist()

                st.session_state["benchmark_chanzfp"] = st.multiselect(
                    label="**Channel + Zone**",
                    options=df_benchmark_stores["CHAN+ZFP"].sort_values().unique().tolist(), 
                    default=df_benchmark_stores["CHAN+ZFP"].unique().tolist(),
                    disabled=True
                    )
            df_benchmark_stores = df_benchmark_stores[
                (df_benchmark_stores['State'].isin(st.session_state['benchmark_states'])) &
                (df_benchmark_stores['CHAN+ZFP'].isin(st.session_state['benchmark_chanzfp']))
            ]

            col1, col2, = st.columns(2)

            with col1:
                if "benchmark_pm" not in st.session_state or (st.session_state["benchmark_pm"] is None):
                    st.session_state["benchmark_pm"] = df_benchmark_stores["Subsidy Program 1"].unique().tolist()
                
                def pm_callback():
                    st.session_state["benchmark_pm"] = st.session_state["new_pm"]

                st.multiselect(
                    label="**Subsidy Program 1**",
                    options=df_benchmark_stores["Subsidy Program 1"].sort_values().unique().tolist(), 
                    default=st.session_state["benchmark_pm"],
                    key="new_pm",
                    on_change=pm_callback
                    )

            with col2:
                if ("benchmark_prr" not in st.session_state) or (st.session_state["benchmark_prr"] is None):
                    st.session_state["benchmark_prr"] = df_benchmark_stores["Subsidy Program 2"].unique().tolist()
                    df_benchmark_stores = df_benchmark_stores[
                        (df_benchmark_stores['State'].isin(st.session_state['benchmark_states'])) &
                        (df_benchmark_stores['CHAN+ZFP'].isin(st.session_state['benchmark_chanzfp'])) &
                        (df_benchmark_stores['Subsidy Program 1'].isin(st.session_state['benchmark_pm']))
                    ]

                def prr_callback():
                    st.session_state["benchmark_prr"] = st.session_state["new_prr"]

                st.multiselect(
                    label="**Subsidy Program 2**",
                    options=df_benchmark_stores["Subsidy Program 2"].sort_values().unique().tolist(), 
                    default=st.session_state["benchmark_prr"],
                    key="new_prr",
                    on_change=prr_callback
                    )
                
                df_benchmark_stores = df_benchmark_stores[
                    (df_benchmark_stores['State'].isin(st.session_state['benchmark_states'])) &
                    (df_benchmark_stores['CHAN+ZFP'].isin(st.session_state['benchmark_chanzfp'])) &
                    (df_benchmark_stores['Subsidy Program 1'].isin(st.session_state['benchmark_pm'])) &
                    (df_benchmark_stores['Subsidy Program 2'].isin(st.session_state['benchmark_prr']))
                ]

                benchmark_address_ids = df_benchmark_stores["address_id"].unique().tolist()

        else:
            col1, col2 = st.columns(2)

            with col1:
                if "custom_benchmark_states" not in st.session_state:
                    st.session_state["custom_benchmark_states"] = df_stores["State"].unique().tolist()

                st.session_state["custom_benchmark_states"] = st.multiselect(
                    label="**State**", 
                    options=df_stores["State"].sort_values().unique().tolist(),
                    default=df_stores["State"].sort_values().unique().tolist(),
                    )

            with col2:
                if "custom_benchmark_chanzfp" not in st.session_state:
                    st.session_state["custom_benchmark_chanzfp"] = df_stores["CHAN+ZFP"].unique().tolist()

                st.session_state["custom_benchmark_chanzfp"] = st.multiselect(
                    label="**Channel + Zone**",
                    options=df_stores["CHAN+ZFP"].sort_values().unique().tolist(), 
                    default=df_stores["CHAN+ZFP"].sort_values().unique().tolist(),
                    )

            col1, col2 = st.columns(2)

            with col1:
                if "custom_benchmark_pm" not in st.session_state:
                    st.session_state["custom_benchmark_pm"] = df_stores["Subsidy Program 1"].unique().tolist()

                st.multiselect(
                    label="**Subsidy Program 1**",
                    options=df_stores["Subsidy Program 1"].sort_values().unique().tolist(), 
                    default=df_stores["Subsidy Program 1"].sort_values().unique().tolist(),
                    )

            with col2:
                if "custom_benchmark_prr" not in st.session_state:
                    st.session_state["custom_benchmark_prr"] = df_stores["Subsidy Program 2"].unique().tolist()

                st.multiselect(
                    label="**Subsidy Program 2**",
                    options=df_stores["Subsidy Program 2"].sort_values().unique().tolist(), 
                    default=df_stores["Subsidy Program 2"].sort_values().unique().tolist(),
                    )

            df_benchmark_stores = df_stores[
                df_stores['State'].isin(st.session_state['custom_benchmark_states']) &
                df_stores['CHAN+ZFP'].isin(st.session_state['custom_benchmark_chanzfp']) &
                df_stores['Subsidy Program 1'].isin(st.session_state['custom_benchmark_pm']) &
                df_stores['Subsidy Program 2'].isin(st.session_state['custom_benchmark_prr'])
            ]

            benchmark_address_ids = df_benchmark_stores["address_id"].unique().tolist()
        
        if "benchmark_address_ids" not in st.session_state: # or (st.session_state['benchmark_address_ids'] is None):
            st.session_state["benchmark_address_ids"] = benchmark_address_ids

        benchmark_table = df_benchmark_stores[[
            "address_id", "Store Name", "State", "CHAN+ZFP", 
            "Subsidy Program 1", "Subsidy Program 2", "Store Size",]].sort_values('address_id')


        gb = GridOptionsBuilder.from_dataframe(benchmark_table)
        gb.configure_column("address_id", headerCheckboxSelection=True)
        gb.configure_default_column(cellStyle={
            # "color": "black", 
            "font-size": "12px"
        }, suppressMenu=True, wrapHeaderText=True, autoHeaderHeight=True) # Suppress Menu disables the column filters
        gb.configure_selection(selection_mode="multiple", use_checkbox=True, pre_select_all_rows=True)
        gridOptions = gb.build()

        column_defs = gridOptions["columnDefs"]
        col_width = [200, 300, 100, 150, 200, 200, 100,]
        for i, col_def in enumerate(column_defs):
            col_def["width"] = col_width[i]
        # custom_css = {
        #     ".ag-header-cell-text": {"font-size": "12px", 'text-overflow': 'revert;', 'font-weight': 700},
        #     ".ag-theme-streamlit": {'transform': "scale(0.8)", "transform-origin": '0 0'}
        # }

        grid_data = AgGrid(
            data=benchmark_table,
            gridOptions=gridOptions,
            # data_return_mode="AS_INPUT",
            # update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            height=666,
            # custom_css=custom_css,
            column_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
            header_checkbox_selection_filtered_only=False,
            use_checkbox=True,
            theme=AgGridTheme.ALPINE,
            # reload_data=True,
            # allow_unsafe_jscode=True,
            # columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            )
        # st.session_state['selected_row_indexes'] = [row['_selectedRowNodeInfo']['nodeRowIndex'] for row in st.session_state['new_row_selection']['selected_rows']]
        # st.session_state['selected_row_indexes'] = [row['_selectedRowNodeInfo']['nodeRowIndex'] for row in grid_data['selected_rows']]

        st.session_state["benchmark_address_ids"] = [row["address_id"] for row in grid_data["selected_rows"]]
        st.markdown(f"**_{len(st.session_state['benchmark_address_ids'])} stores in benchmark group_**")

