BASE_TABLE_DICTIONARY = {
    "orders": {
        "description": "Order lifecycle and delivery timestamps.",
        "primary_key": "order_id",
        "fields": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        "join_keys": {
            "customers": "customer_id",
            "order_items": "order_id",
            "payments": "order_id",
            "order_reviews": "order_id",
        },
    },
    "order_items": {
        "description": "Order item lines with product, seller, price, and freight.",
        "primary_key": ["order_id", "order_item_id"],
        "fields": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
        "join_keys": {
            "orders": "order_id",
            "products": "product_id",
            "sellers": "seller_id",
        },
    },
    "products": {
        "description": "Product category and physical attributes.",
        "primary_key": "product_id",
        "fields": [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
        "join_keys": {
            "order_items": "product_id",
            "product_category_name_translation": "product_category_name",
        },
    },
    "customers": {
        "description": "Customer identity and geographic location.",
        "primary_key": "customer_id",
        "fields": [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
        "join_keys": {
            "orders": "customer_id",
            "geolocation": "customer_zip_code_prefix",
        },
    },
    "sellers": {
        "description": "Seller identity and geographic location.",
        "primary_key": "seller_id",
        "fields": [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
        "join_keys": {
            "order_items": "seller_id",
            "geolocation": "seller_zip_code_prefix",
        },
    },
    "payments": {
        "description": "Payment method, installments, and transaction value.",
        "primary_key": ["order_id", "payment_sequential"],
        "fields": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
        "join_keys": {
            "orders": "order_id",
        },
    },
    "order_reviews": {
        "description": "Customer review score, title, message, and review timestamps.",
        "primary_key": "review_id",
        "fields": [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
        "join_keys": {
            "orders": "order_id",
        },
    },
    "geolocation": {
        "description": "Brazil zip-code geolocation reference.",
        "primary_key": None,
        "fields": [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ],
        "join_keys": {
            "customers": "customer_zip_code_prefix",
            "sellers": "seller_zip_code_prefix",
        },
    },
    "product_category_name_translation": {
        "description": "Portuguese-to-English product category translation.",
        "primary_key": "product_category_name",
        "fields": [
            "product_category_name",
            "product_category_name_english",
        ],
        "join_keys": {
            "products": "product_category_name",
        },
    },
}


VIEW_DICTIONARY = {
    "mv_monthly_sales": {
        "description": "Monthly sales trend view.",
        "granularity": "year_month",
        "fields": [
            "ym",
            "total_gmv",
            "total_orders",
            "avg_basket",
            "total_freight",
        ],
        "preferred_for": [
            "monthly sales trend",
            "GMV trend",
            "average basket analysis",
        ],
    },
    "mv_state_sales": {
        "description": "Monthly sales by customer state.",
        "granularity": "year_month, customer_state",
        "fields": [
            "ym",
            "customer_state",
            "total_gmv",
            "total_orders",
            "unique_customers",
        ],
        "preferred_for": [
            "state sales ranking",
            "regional sales comparison",
            "customer distribution by state",
        ],
    },
    "mv_category_sales": {
        "description": "Monthly sales by product category.",
        "granularity": "year_month, product_category",
        "fields": [
            "ym",
            "product_category",
            "total_gmv",
            "total_orders",
            "avg_price",
        ],
        "preferred_for": [
            "category performance",
            "top categories",
            "category price analysis",
        ],
    },
    "mv_delivery_perf": {
        "description": "Monthly delivery performance by customer state.",
        "granularity": "year_month, customer_state",
        "fields": [
            "ym",
            "customer_state",
            "avg_delivery_days",
            "on_time_rate",
            "delayed_orders",
        ],
        "preferred_for": [
            "delivery delay diagnosis",
            "on-time delivery rate",
            "state delivery performance",
        ],
    },
    "mv_seller_perf": {
        "description": "Monthly seller performance with sales and review score.",
        "granularity": "year_month, seller_id, seller_state",
        "fields": [
            "ym",
            "seller_id",
            "seller_state",
            "total_gmv",
            "total_orders",
            "avg_review_score",
        ],
        "preferred_for": [
            "seller performance",
            "low-rated sellers",
            "seller review monitoring",
        ],
    },
    "mv_payment_dist": {
        "description": "Monthly payment type and installment distribution.",
        "granularity": "year_month, payment_type",
        "fields": [
            "ym",
            "payment_type",
            "total_transactions",
            "avg_installments",
            "total_value",
        ],
        "preferred_for": [
            "payment preference",
            "installment analysis",
            "payment transaction distribution",
        ],
    },
}


DATA_DICTIONARY = {
    "base_tables": BASE_TABLE_DICTIONARY,
    "preaggregated_views": VIEW_DICTIONARY,
}
