import streamlit as st

def render_page():
    st.title('User Guide 📖')
    st.markdown(
        """
        _This is a heavily stripped down tool used in-house for tracking and analytical purposes._
        ___

        **⚠️ THE DATA IS FAKE!** Obviously, duh! 😆
        ___

        **⚙️Store Selection Tab:**
        - Pick a store.
        - It will generate a benchmark list of stores with comparable attributes.
        - You can customise the list using the [streamlit-aggrid](https://github.com/PablocFonseca/streamlit-aggrid). It's not as good as the real AgGrid from Plotly but it's good enough! 🤷‍♂️
        - The target store and benchmark list is linked to all other pages by session states.
        <br></br>

        **📈Sales/GP/Units Tab:**
        - Default view is of Target Store vs Benchmark Stores (the clickable headers denote what is what i.e. Target Store on left and Benchmark on right).
        - The horizontal tab and the side bar is done using [streamlit-option-menu](https://github.com/victoryhb/streamlit-option-menu).
        - You can zoom and do other stuff if you mouse hover and click those little icons on the top right of a particular chart.
        - Everything is linked by session states, even across pages e.g. the selected Periodicity, Promotion Status etc. will carry over to other pages with these fields.
        <br></br>

        **⚖️Benchmarking:**
        - Indexes starting point of target store and benchmark group to 100 at the benchmark start date.
        - This way you can see volatility of sales compare to benchmark (think of beta in CAPM). Can see stores with high seasonality e.g. holiday spots.
        - Cumulative Index shows outperformance/underperformance over the benchmark period.
        - Bubble chart shows performance on a per sqm basis. Click the play button to see how square footage performance varies month to month. Stores with high seasonality will jump wildly.
        <br></br>
        
        **🛒Baskets:**
        - Pretty self explanatory...
        <br></br>

        **📦Sales Profile:** 
        - Double click on items on the legend to single out that item on the charts. 
        - Double click on the white space on the legend to reset.
        <br></br>
        
        **🖥️ Redshift Interface:**
        - Demonstrates that Streamlit can be used as a UI for SQL queries.
        - Useful for non-technical team members who need to regularly pull data where only certain fields need to be changed in an otherwise static query e.g. date range.
        - Schema/table column names have been changed, and you won't find the credentials in the git commit history. 🙃
        <br></br>

        **🖥️ SQL GUI:**
        - Not related or linked to any session states. Just demonstrating how Streamlit can be used to empower non-tech users to extract SQL data for themselves.
        - More input fields for SQL querying.
        - More dynamic ways of altering a SQL query depending on input parameters.
        """
    , unsafe_allow_html=True
    )