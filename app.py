import streamlit as st
from streamlit_option_menu import option_menu
from tabs import (
    user_guide,
    store_selection,
    sales_gp_units,
    sales_gp_units_benchmark,
    baskets,
    sales_profile,
    redshift_interface,
    sql_gui
)


# Page Config & Emoji
st.set_page_config(
    layout="wide",
    page_title="Store Analytics",
    page_icon="📈"
)

app_custom_css= \
    """
    <style>
        [data-testid="stSidebar"][aria-expanded="true"]{
            min-width: 200px;
            max-width: 240px;
        }
        /* Hide the super thin reddish glowing bar at the top */
        .css-vk3wp9 {
            top: 0px;
        }
        .css-1dp5vir {
            height: 0px;
        }
        /* Padding for top of page */
        .css-z5fcl4 {
            padding-left: 5rem;
            padding-right: 5rem;
            padding-top: 2rem;
        }
        /* Sidebar background color */
        .css-6qob1r {
            background-color: #0e1012
        }
        /* Button to close and re-open sidebar */
        .css-hq57x2 {               
            color: grey;
        }
        .css-6qob1r {
            color: white;
        }
        .css-1544g2n {
            padding: 3rem 1rem 1rem;
        }

        div[data-testid="stMarkdownContainer"] p {
            font-size: 1rem;
        }   
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
            background-color: #2979bf;
            border-color: #EEEEEE;
            color: #FFFFFF;
        }
        div.stDownloadButton > button {
            background-color: #2979bf;
            border-color: #FFFFFF;
            color: #FFFFFF;
        }
        div.stDownloadButton > button:hover {
            background-color: #2979bf;
            border-color: #00008B;
            color: #FFFFFF;
        }
        div[data-testid="stExpander"] div[role="button"] p {
            font-size: 15px;
            # font-weight: 600;
        }
        /* Allow for thiiicccc and chonky wide multiselect tabs */
        .stMultiSelect [data-baseweb=select] span{
            max-width: 500px;
        }
        /* #MainMenu {visibility: hidden;} */
        /*header {visibility: hidden;} */
        footer {visibility: hidden;}
    </style>
    """
st.markdown(app_custom_css, unsafe_allow_html=True)


with st.sidebar:
    selected_page = option_menu(
        menu_title="Store Analytics",
        options=["User Guide", 
                 "---",
                 "Store Selection", 
                 "---", 
                 "Sales/GP/Units",
                 "Benchmarking",
                 "Baskets",
                 "Sales Profile",
                 "---",
                 "Redshift Interface",
                 "---",
                 "SQL GUI"], 
        icons=["info-circle", 
               "---", 
               "gear-fill", 
               "---", 
               "bar-chart",
               "graph-up",
               "cart",
               "boxes",
               "---",
               "server",
               "---",
               "display"],
        menu_icon="None",
        default_index=2,
        styles={
            "container": {
                "border-radius": "0rem",
                "background-color": "#0e1012",
                "align-items": "stretch",
                "font-size": "13x",
                "font-weight": "500",
                "padding": "0rem !important"
            },
            "menu-title": {
                "color": "white",
                "font-size": "23px",
                "font-weight": "bold",
                "text-align": "left",
                "padding-top": ".5rem",
                "padding-left": "0rem",
                "padding-right": "0rem",
                "margin-left": "0rem !important",
                "margin-right": "0rem !important"
            },
            "nav-link": {
                "color": "white",
                "font-size": "15px",
                "font-weight": "500",
                "--hover-color": "#3c3c3c",
                "text-align": "left",
                "padding-left": "0.3rem",
                "padding-right": "0.3rem"
            },
            "nav-link-selected": {
                "background-color": "#303030",
                "font-size": "15px",
                "font-weight": "600"
            }
        }
    )

def render_no_data_warning():
    st.warning("Please select a target store in the **Store Selection** tab")

try:
    if selected_page == "User Guide":
        user_guide.render_page()
        print("Page Selected -> User Guide")

    if selected_page == "Store Selection":
        store_selection.render_page()
        print("Page Selected -> Store Selection")

    if selected_page == "Sales/GP/Units":
        print("Page Selected -> Sales/GP/Units")
        if "target_address_id" not in st.session_state:
            render_no_data_warning()
        else:
            sales_gp_units.render_page()

    if selected_page == "Benchmarking":
        print("Page Selected -> Sales/GP/Units BENCHMARK")
        if "target_address_id" not in st.session_state:
            render_no_data_warning()
        else:
            sales_gp_units_benchmark.render_page()
            
    if selected_page == "Baskets":
        print("Page Selected -> Baskets")
        if "target_address_id" not in st.session_state:
            render_no_data_warning()
        else:
            baskets.render_page()

    if selected_page == "Sales Profile":
        print("Page Selected -> Synoptic Measures")
        if "target_address_id" not in st.session_state:
            render_no_data_warning()
        else:
            sales_profile.render_page()

    if selected_page == "Redshift Interface":
        print("Page Selected -> Redshift Interface")
        if "target_address_id" not in st.session_state:
            render_no_data_warning()
        else:
            redshift_interface.render_page()
    
    if selected_page == "SQL GUI":
        print("Page Selected -> SQL GUI")
        sql_gui.render_page()
            
except KeyError:
    pass
 