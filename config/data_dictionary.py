VIEW_DICTIONARY = {

    "mv_monthly_sales": {
        "description": "月销售趋势",
        "fields": [
            "ym",
            "total_gmv",
            "total_orders",
            "avg_basket",
            "total_freight"
        ]
    },

    "mv_state_sales": {
        "description": "州销售分析",
        "fields": [
            "ym",
            "customer_state",
            "total_gmv",
            "total_orders",
            "unique_customers"
        ]
    },

    "mv_category_sales": {
        "description": "品类分析",
        "fields": [
            "ym",
            "product_category",
            "total_gmv",
            "total_orders",
            "avg_price"
        ]
    }

}