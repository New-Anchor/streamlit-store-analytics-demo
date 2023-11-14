import pandas as pd
import plotly.graph_objects as go


COLOR_SCHEME = ["rgb(133, 133, 166)", # 2019
                "rgb(33, 66, 33)", # 2020
                "rgb(0, 84, 165)", # 2021
                "rgb(26, 118, 255)", # 2022
                "rgb(255, 128, 0)"] # 2023


SELECTBOX_TO_COLNAME_DICT = {
    'YoY - Quarterly': 'lped_qtr_nm',
    'YoY - Monthly': 'prom_mth_num',
    'YoY - Weekly': 'prom_year_wk_num',
    'Quarterly': 'lped_qtr_yr_dt',
    'Monthly': 'prom_mth_yr_dt',
    'Weekly': 'prom_wk_end_dt',
}


class ChartCalendarDates:
    def __init__(self, df_benchmark_stores):
        self.df_qtrs_yoy = df_benchmark_stores[['lped_qtr_nm', 'lped_year_num']].drop_duplicates()
        self.df_months_yoy = df_benchmark_stores[['prom_mth_num', 'prom_year_num']].drop_duplicates()
        self.df_wk_nums_yoy = df_benchmark_stores[['prom_year_wk_num', 'prom_year_num']].drop_duplicates()
        self.df_qtrly = df_benchmark_stores[['lped_qtr_yr_dt', 'lped_year_num']].drop_duplicates()
        self.df_monthly = df_benchmark_stores[['prom_mth_yr_dt', 'prom_year_num']].drop_duplicates()
        self.df_wk_start_dts = df_benchmark_stores[['prom_wk_end_dt', 'prom_year_num']].drop_duplicates()
        self.df_period = {
            'lped_qtr_nm': self.df_qtrs_yoy,
            'prom_mth_num': self.df_months_yoy,
            'prom_year_wk_num': self.df_wk_nums_yoy,
            'lped_qtr_yr_dt': self.df_qtrly,
            'prom_mth_yr_dt': self.df_monthly,
            'prom_wk_end_dt': self.df_wk_start_dts
        }


class SalesChartDataframeCreator(ChartCalendarDates):
    """
    TODO - 
    Should I make the methods much simpler? i.e. only create the specific dataframe needed 
    rather than all this convoluted shit where the last method acts like main().
    Add a method that parses the parameters and runs the required method.
    Shorten code here but will lengthen code in spawn chart 🙃🤔
    """
    def __init__(self, df_benchmark_stores):
        super().__init__(df_benchmark_stores)
        
    def make_groupby_period_df(self, df, metric, periodicity, year_col_name, agg_method):
        df_agg = df.groupby([periodicity, year_col_name])[metric].sum().reset_index()
        if agg_method == 'Average per Store':
            store_count = len(df['address_id'].unique())
            df_agg[metric] = round(df_agg[metric] / store_count, 2)
        df_agg_final = pd.merge(
            self.df_period[periodicity], df_agg, how='left', on=[periodicity, year_col_name]
        ).sort_values([year_col_name, periodicity], ascending=[True, True])
        return df_agg_final
    
    def make_pct_total_df(self, df, metric, periodicity, year_col_name, indicator_column, agg_method):
        df_total = df.groupby([periodicity, year_col_name])[metric].sum().reset_index()
        if agg_method == 'Average per Store':
            store_count = len(df['address_id'].unique())
            df_total[metric] = round(df_total[metric] / store_count, 2)
        df_total = df_total.rename(columns={metric: 'metric_total'})

        df_indicator = df[df[indicator_column] == 'Y'].groupby([periodicity, year_col_name])[metric].sum().reset_index()
        if agg_method == 'Average per Store':
            store_count = len(df['address_id'].unique())
            df_indicator[metric] = round(df_indicator[metric] / store_count, 2)

        df_ratio = pd.merge(df_total, df_indicator, how='outer', on=[periodicity, year_col_name])
        df_ratio[f'{indicator_column} {metric} ratio'] = round(df_ratio[metric] / df_ratio['metric_total'], 4)
        df_ratio = df_ratio.drop([metric, 'metric_total'], axis=1)
        return df_ratio
    
    def make_gp_pct_df(self, df, periodicity, year_col_name, agg_method):
        df_gp_agg = df.groupby([periodicity, year_col_name])[['gp_ex_gst', 'sales_ex_gst']].sum().reset_index()
        if agg_method == 'Average per Store':
            store_count = len(df['address_id'].unique())
            df_gp_agg[['gp_ex_gst', 'sales_ex_gst']] = round(df_gp_agg[['gp_ex_gst', 'sales_ex_gst']] / store_count, 2)
        df_gp_agg['gp_pct'] = df_gp_agg['gp_ex_gst'] / df_gp_agg['sales_ex_gst']
        # Joined with DF_QTRS to make sure new stores will display all the time axis
        df_gp_agg_final = pd.merge(
            self.df_period[periodicity], df_gp_agg, how='left', on=[periodicity, year_col_name]
        )[[periodicity, year_col_name, 'gp_pct']].sort_values([year_col_name, periodicity], ascending=[True, True])
        return df_gp_agg_final
    
    def make_sales_chart_input_df(self, df, metric, st_ss_periodicity, st_ss_agg_method):
        periodicity = SELECTBOX_TO_COLNAME_DICT[st_ss_periodicity]
        if 'lped_' in periodicity:
            year_col_name = 'lped_year_num'
        else:
            year_col_name = 'prom_year_num'
        df_chart = self.make_groupby_period_df(df, metric, periodicity, year_col_name, agg_method=st_ss_agg_method).merge(
            self.make_pct_total_df(df, metric, periodicity, year_col_name, indicator_column='warehouse', agg_method=st_ss_agg_method), 
            on=[periodicity, year_col_name], how='left'
        ).merge(
            self.make_gp_pct_df(df, periodicity, year_col_name, agg_method=st_ss_agg_method),
            on=[periodicity, year_col_name], how='left'
        ).merge(
            self.make_pct_total_df(df, metric, periodicity, year_col_name, indicator_column='promotion_ind', agg_method=st_ss_agg_method), 
            on=[periodicity, year_col_name], how='left'
        )
        return df_chart


class BasketsChartDataframeCreator(ChartCalendarDates):
    def __init__(self, df_benchmark_stores):
        super().__init__(df_benchmark_stores)

    def make_basket_chart_df(self, df, metric, st_ss_periodicity):
        self.periodicity = SELECTBOX_TO_COLNAME_DICT[st_ss_periodicity]
        if 'lped_' in self.periodicity:
            self.year_col_name = 'lped_year_num'
        else:
            self.year_col_name = 'prom_year_num'

        # if metric == 'store_baskets':
        #     df = df.groupby([self.periodicity, self.year_col_name])[metric].sum().reset_index()
        # else:
        #     df = round(df.groupby([self.periodicity, self.year_col_name])[metric].mean().reset_index(), 2)

        df = round(df.groupby([self.periodicity, self.year_col_name])[metric].mean().reset_index(), 2)
        df = pd.merge(
            self.df_period[self.periodicity], df, how='left', on=[self.periodicity, self.year_col_name]
        ).sort_values([self.year_col_name, self.periodicity], ascending=[True, True])
        return df

    def make_basket_chart_input_df(self, df, st_ss_periodicity):
        col_name_list = ['store_baskets', 'store_avg_basket_size', 'store_avg_basket_value']
        dfs = [self.make_basket_chart_df(df, col_name, st_ss_periodicity) for col_name in col_name_list]
        dfs = [df.set_index([self.periodicity, self.year_col_name]) for df in dfs]
        return dfs[0].join(dfs[1:], how='inner').reset_index()


class Charts:
    def __init__(self, color_scheme=COLOR_SCHEME):
        self.color_scheme_list = color_scheme
        
    @staticmethod
    def create_x_axis(df, st_ss_periodicity):
        if st_ss_periodicity == 'YoY - Monthly':
            x_axis = pd.to_datetime(df[SELECTBOX_TO_COLNAME_DICT[st_ss_periodicity]], format='%m').unique()
        elif st_ss_periodicity == 'Monthly':
            x_axis = pd.to_datetime(df[SELECTBOX_TO_COLNAME_DICT[st_ss_periodicity]], format='%m-%Y').unique()
        else:
            x_axis = df[SELECTBOX_TO_COLNAME_DICT[st_ss_periodicity]].unique()
        return x_axis
    
    @staticmethod
    def parse_year_col_name(st_ss_periodicity):
        if 'Quarterly' in st_ss_periodicity:
            return 'lped_year_num'
        else:
            return 'prom_year_num'
        
    def make_barchart_yoy(self, df, metric, metric_renamed, st_ss_periodicity):
        self.metric = metric
        self.metric_renamed = metric_renamed
        self.st_ss_periodicity = st_ss_periodicity
        year_col_name = self.parse_year_col_name(st_ss_periodicity)
        self.years = df[year_col_name].unique()
        self.x_axis = self.create_x_axis(df, st_ss_periodicity)
        self.fig = go.Figure()
        for year, bar_color in zip(self.years, self.color_scheme_list):
            name = f"{year} {metric_renamed}"
            if metric in ['sales_qty', 'store_baskets', 'store_avg_basket_size']:
                hovertemplate = f"{name}: %{{y:.3s}}<extra></extra>"
            else:
                hovertemplate = f"{name}: %{{y:$.3s}}<extra></extra>"
            y_axis = df[df[year_col_name] == year][metric]
            self.fig.add_trace(
                go.Bar(
                    name=name,
                    x=self.x_axis,
                    y=y_axis,
                    marker_color=bar_color,
                    hovertemplate=hovertemplate
                )
            )
        return self
              
    def make_ratio_linechart_yoy(self, df, metric, metric_renamed, st_ss_periodicity, indicator='gp_pct'):
        self.indicator = indicator
        self.metric_renamed = metric_renamed
        self.st_ss_periodicity = st_ss_periodicity
        year_col_name = self.parse_year_col_name(st_ss_periodicity)
        self.years = df[year_col_name].unique()
        self.x_axis = self.create_x_axis(df, st_ss_periodicity)
        self.fig = go.Figure()
        for year, line_color in zip(self.years, self.color_scheme_list):
            name = f"{year} {metric_renamed}"
            if indicator == 'gp_pct':
                self.indicator_renamed = 'GP%'
                name = f"{year} GP%"
                y_axis = df[df[year_col_name] == year]['gp_pct']
                hovertemplate = f"{name}: %{{y:.1%}}<extra></extra>"
                line_shape = "hvh"
            else:
                indicator_dict = {'warehouse': 'Warehouse', 'promotion_ind': 'Promotions'}
                self.indicator_renamed = indicator_dict[indicator]
                name = f"{year} % {self.indicator_renamed}"
                y_axis = df[df[year_col_name] == year][f'{indicator} {metric} ratio']
                hovertemplate = f"{name}: %{{y:.1%}}<extra></extra>"
                line_shape = "linear"

            self.fig.add_trace(
                go.Scatter(
                    name=name,
                    x=self.x_axis,
                    y=y_axis,
                    marker_color=line_color,
                    mode="lines+markers",
                    line_shape=line_shape,
                    hovertemplate = hovertemplate,
                )
            )
        return self

    def make_barchart_timeseries(self, df, metric, metric_renamed, st_ss_periodicity):
        self.metric = metric
        self.metric_renamed = metric_renamed
        self.st_ss_periodicity = st_ss_periodicity
        self.x_axis = self.create_x_axis(df, st_ss_periodicity)
        y_axis = df[metric]
        name=f"{st_ss_periodicity} {metric_renamed}"
        if metric in ['sales_qty', 'store_baskets', 'store_avg_basket_size']:
            hovertemplate = f"{name}: %{{y:.3s}}<extra></extra>"
        else:
            hovertemplate = f"{name}: %{{y:$.3s}}<extra></extra>"
        self.fig = go.Figure()    
        self.fig.add_trace(
            go.Bar(
                x=self.x_axis,
                y=y_axis,
                hovertemplate=hovertemplate
            )
        )
        return self
                
    def make_linechart_timeseries(self, df, metric, metric_renamed, st_ss_periodicity):
        self.x_axis = self.create_x_axis(df, st_ss_periodicity)
        y_axis = df[metric]
        self.fig = go.Figure()    
        self.fig.add_trace(
            go.Scatter(
                name=f"{st_ss_periodicity} {metric_renamed}",
                x=self.x_axis,
                y=y_axis,
                mode="lines",
                line_shape="spline",
                hovertemplate=f"{metric_renamed}: %{{y:$.3s}}<extra></extra>"
            )
        )
        self.fig.update_layout(
            height=233,
            title=f"{metric_renamed} - {st_ss_periodicity}",
            yaxis_title=f"{metric_renamed}",
            xaxis=dict(tickfont_size=16),
            yaxis=dict(
                tickfont_size=16,
                tickformat="$,.3s",
                showspikes=True,
            ),
            hovermode="x unified",
            margin=dict(t=33, b=33),
        )
        return self
    
    
    def make_ratio_linechart_timeseries(self, df, metric, st_ss_periodicity, indicator='gp_pct'):
        self.x_axis = self.create_x_axis(df, st_ss_periodicity)
        self.fig = go.Figure()
        if indicator == 'gp_pct':
            indicator_renamed = 'GP%'
            y_axis = df['gp_pct']
            hovertemplate = f"GP%: %{{y:.1%}}<extra></extra>"
            line_shape = "hvh"
            title=f"{indicator_renamed} - {st_ss_periodicity}"
        else:
            indicator_dict = {'warehouse': 'Warehouse', 'promotion_ind': 'Promotions'}
            indicator_renamed = indicator_dict[indicator]
            y_axis = df[f'{indicator} {metric} ratio']
            hovertemplate = f"% {indicator_renamed}: %{{y:.1%}}<extra></extra>"
            line_shape = "linear"
            title=f"% {indicator_renamed} - {st_ss_periodicity}"
            

        self.fig.add_trace(
            go.Scatter(
                x=self.x_axis,
                y=y_axis,
                mode="lines+markers",
                line_shape=line_shape,
                hovertemplate = hovertemplate,
            )
        )
        self.fig.update_layout(
            height=233,
            title=title,
            yaxis_title=f"{indicator_renamed}",
            xaxis=dict(tickfont_size=16),
            yaxis=dict(
                tickfont_size=16,
                tickformat=",.1%",
                showspikes=True,
            ),
            hovermode="x unified",
            margin=dict(t=33, b=33),
        )
        return self
                
    
    def make_linechart_timeseries(self, df, metric, metric_renamed, st_ss_periodicity, indicator=None):
        self.x_axis = self.create_x_axis(df, st_ss_periodicity)
        if indicator is None:
            y_axis = df[metric]
            if metric in ['sales_qty', 'store_baskets']:
                y_tickformat = ",.3s"
            else:
                y_tickformat = "$,.3s"
            hovertemplate=f"{metric_renamed}: %{{y:{y_tickformat}}}<extra></extra>"
            line_shape="spline"
            title=f"{metric_renamed} - {st_ss_periodicity}"
            yaxis_title=f"{metric_renamed}"
        elif indicator == 'gp_pct':
            y_axis = df['gp_pct']
            y_tickformat=",.0%"
            indicator_renamed = 'GP%'
            hovertemplate = f"GP%: %{{y:.1%}}<extra></extra>"
            line_shape = "hvh"
            title=f"{indicator_renamed} - {st_ss_periodicity}"
            yaxis_title=f"{indicator_renamed}"
        else:
            y_axis = df[f'{indicator} {metric} ratio']
            y_tickformat=",.0%"
            indicator_dict = {'warehouse': 'Warehouse', 'promotion_ind': 'Promotions'}
            indicator_renamed = indicator_dict[indicator]
            hovertemplate = f"% {indicator_renamed}: %{{y:.1%}}<extra></extra>"
            line_shape = "spline"
            title=f"% {indicator_renamed} - {st_ss_periodicity}"
            yaxis_title=f"{indicator_renamed}"
        
        self.fig = go.Figure()  
        self.fig.add_trace(
            go.Scatter(
                x=self.x_axis,
                y=y_axis,
                mode="lines",
                line_shape=line_shape,
                hovertemplate = hovertemplate,
            )
        )
        self.fig.update_layout(
            height=233,
            title=title,
            yaxis_title=yaxis_title,
            xaxis=dict(tickfont_size=16),
            yaxis=dict(
                tickfont_size=16,
                tickformat=y_tickformat,
                showspikes=True,
            ),
            hovermode="x unified",
            margin=dict(t=33, b=33),
        )
        return self


class ChartMaker(Charts):
    def __init__(self):
        super().__init__(color_scheme=COLOR_SCHEME)
        
    def format_barchart_yoy(self):
        if self.metric in ['sales_qty', 'store_baskets', 'store_avg_basket_size']:
            y_tickformat = ",.0s"
        else:
            y_tickformat = "$,.0s"
        self.fig.update_layout(
            height=233,
            title=f"{self.metric_renamed} - {self.st_ss_periodicity}",
            yaxis_title=self.metric_renamed,
            hovermode="x unified",
            margin=dict(t=33, b=33),
            xaxis=dict(
                tickfont_size=16,
                tickvals=self.x_axis,
                tickformat="%b",
                color="#C0C0C0",
            ),
            yaxis=dict(
                tickfont_size=16,
                tickformat=y_tickformat
            ),
            barmode="group",
            bargap=0.1, # gap between bars of adjacent location coordinates.
            bargroupgap=0.05 # gap between bars of the same location coordinate.
        )
        return self.fig
    
    def format_ratio_linechart_yoy(self):
        if self.indicator == 'gp_pct':
            title = f"{self.indicator_renamed} - {self.st_ss_periodicity}"
            yaxis_title = f"{self.indicator_renamed}"
        else:            
            title = f"% {self.indicator_renamed} - {self.st_ss_periodicity}"
            yaxis_title = f"% {self.indicator_renamed}"  
        self.fig.update_layout(
            height=233,
            title=title,
            yaxis_title=yaxis_title,
            hovermode="x unified",
            margin=dict(t=33, b=33),
            xaxis=dict(
                tickfont_size=16,
                tickvals=self.x_axis,
                tickformat="%b",
                color="#C0C0C0",
            ),
            yaxis=dict(
                tickfont_size=16,
                tickformat=",.0%",
            )
        )
        return self.fig

    def format_barchart_timeseries(self):
        if self.metric in ['sales_qty', 'store_baskets', 'store_avg_basket_size']:
            y_tickformat = ",.0s"
        else:
            y_tickformat = "$,.0s"

        if self.st_ss_periodicity == 'Weekly':
            x_tickformat = "%Y-%b-%d"
            x_tickvals = None
        else:
            x_tickformat = "%b-%Y"
            x_tickvals = self.x_axis

        self.fig.update_layout(
            height=233,
            title=f"{self.metric_renamed} - {self.st_ss_periodicity}",
            yaxis_title=f"{self.metric_renamed}",
            xaxis=dict(
                tickfont_size=16,
                tickvals=x_tickvals,
                tickformat=x_tickformat,
                color="#C0C0C0",
            ),
            yaxis=dict(
                tickfont_size=16,
                tickformat=y_tickformat,
                showspikes=True,
            ),
            hovermode="x unified",
            margin=dict(t=33, b=33),
        )
        return self.fig
