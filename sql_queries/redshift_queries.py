
def scan_sales_query(address_id, start_date, end_date):
    return f"""
        WITH
            filtered_table AS ( 
                SELECT f.date_id, f.address_id, f.basket_number, f.basket_dtm, 
                       p.finance_department_nm, p.dept_nm, p.category_nm, p.commodity_nm,
                       s.store_nm, s.state_nm, p.product_cd, p.product_desc,
                       f.promo_flg, f.sales_qty, f.sales_excl_gst, f.cost_excl_gst, f.gross_profit,
                       d.fisc_date
                FROM schema_x.scan_sales AS f
                INNER JOIN schema_x.dw_dim_product AS p 
                        ON f.product_id = p.product_id
                INNER JOIN schema_x.dw_dim_date AS d 
                        ON f.date_id = d.date_id
                INNER JOIN schema_x.dim_store AS s
                        ON f.address_id = s.address_id
                WHERE f.address_id = {address_id}
                  AND d.fisc_date BETWEEN '{start_date}' AND '{end_date}'
            ),
                
            drop_duplicates_table AS (
                SELECT DISTINCT ft.date_id, ft.address_id, ft.basket_number, ft.basket_dtm, 
                                ft.finance_department_nm, ft.dept_nm, ft.category_nm, ft.commodity_nm, 
                                ft.store_nm, ft.state_nm, ft.product_cd, ft.product_desc,
                                ft.promo_flg, ft.sales_qty, ft.sales_excl_gst, ft.cost_excl_gst, ft.gross_profit,
                                ft.fisc_date
                FROM filtered_table AS ft
            ),
                
            promo_ind AS (
                SELECT DISTINCT ft.address_id, ft.basket_number, ft.basket_dtm, ft.product_cd, ft.promo_flg, ft.fisc_date
                FROM filtered_table AS ft
                WHERE ft.sales_qty > 0
            ),
                
            scanned_sales AS (        
                SELECT ddt.date_id, ddt.address_id, ddt.basket_number, ddt.basket_dtm, 
                       ddt.dept_nm, ddt.category_nm, ddt.commodity_nm,
                       ddt.store_nm, ddt.finance_department_nm, ddt.state_nm, 
                       ddt.product_cd, ddt.product_desc, promo_ind.promo_flg, 
                       SUM(ddt.sales_qty) AS nett_sales_qty, SUM(ddt.sales_excl_gst) AS nett_sales_ex_gst, 
                       SUM(ddt.cost_excl_gst) AS nett_cost_ex_gst, SUM(ddt.gross_profit) AS nett_gp_ex_gst,
                       (nett_sales_ex_gst - nett_cost_ex_gst) AS gp_ex_gst, 
                       (gp_ex_gst / NULLIF(nett_cost_ex_gst, 0)) AS gp_pct,
                       ddt.fisc_date
                FROM drop_duplicates_table AS ddt
                INNER JOIN promo_ind
                        ON promo_ind.address_id = ddt.address_id
                       AND promo_ind.basket_number = ddt.basket_number
                       AND promo_ind.basket_dtm = ddt.basket_dtm
                       AND promo_ind.product_cd = ddt.product_cd
                       AND promo_ind.fisc_date = ddt.fisc_date 
                GROUP BY ddt.date_id, ddt.address_id, ddt.basket_number, ddt.basket_dtm, ddt.store_nm, ddt.state_nm, 
                         ddt.finance_department_nm, ddt.dept_nm, ddt.category_nm, ddt.commodity_nm,
                         ddt.product_cd, ddt.product_desc, promo_ind.promo_flg, ddt.fisc_date
                HAVING nett_sales_qty != 0
                   AND nett_cost_ex_gst != 0
                   AND nett_sales_ex_gst != 0
                   AND gp_pct < 1 AND gp_pct > -0.5
            )

        SELECT ss.product_cd, ss.product_desc, ss.promo_flg,
               SUM(ss.nett_sales_qty) AS sales_qty,
               ROUND(SUM(ss.nett_sales_ex_gst), 2) AS sales_ex_gst,
               ROUND(SUM(ss.nett_cost_ex_gst), 2) AS cost_ex_gst,
               (sales_ex_gst - cost_ex_gst) AS gp_ex_gst,
               COUNT(DISTINCT ss.fisc_date) AS total_days,
               ROUND(sales_ex_gst / sales_qty, 2) AS avg_sell_ex_gst,
               ROUND(sales_qty / total_days, 2) AS sales_qty_per_day,
               ss.finance_department_nm, ss.dept_nm, ss.category_nm, ss.commodity_nm
        FROM scanned_sales AS ss
        GROUP BY ss.product_cd, ss.product_desc, ss.promo_flg, 
                 ss.finance_department_nm, ss.dept_nm, ss.category_nm, ss.commodity_nm
        ORDER BY product_cd, promo_flg ASC
        """


def unique_products_query(address_id, start_date, end_date, periodicity):
    if periodicity == 'Weekly':
        period = 'd.prom_wk_end_dt'
    elif periodicity == 'Monthly':
        period = 'd.prom_month_nm, d.prom_year_num'
    return f"""
        SELECT f.address_id, s.store_nm, s.state_nm,
               COUNT(DISTINCT(p.product_cd)), f.promo_flg, {period}
        FROM schema_x.scan_sales AS f
        INNER JOIN schema_x.dw_dim_product AS p
                ON f.product_id = p.product_id
        INNER JOIN schema_x.dw_dim_date AS d
                ON f.date_id = d.date_id
        INNER JOIN schema_x.dim_store AS s
                ON f.address_id = s.address_id
        WHERE f.address_id = {address_id}
          AND d.prom_wk_end_dt BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY f.address_id, s.store_nm, s.state_nm,
                 f.promo_flg, {period}
        """
