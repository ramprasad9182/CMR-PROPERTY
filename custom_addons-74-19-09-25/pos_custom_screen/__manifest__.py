# -*- coding: utf-8 -*-
{
    'name': "pos_custom_screen",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,
    'license': 'LGPL-3',

    'author': "My Company",
    'website': "https://www.github.com//capchi079",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'point_of_sale'],
    'images': ['static/description/newps.png'],
    # always loaded
    'data': [
        "security/ir.model.access.csv",
        # "views/food_court_views.xml",
        "views/food_court_dashboard_action.xml",
        # "reports/food_court_receipt.xml",
        "views/food_court_issue.xml",
        "views/recharge_card.xml",
        "views/return_card.xml",
        "views/pos_history.xml",
    ],

    "assets": {
        "web.assets_backend": [
            # "pos_custom_screen/static/src/css/food_court.css",
            'pos_custom_screen/static/src/css/food_court.scss',
            "pos_custom_screen/static/src/xml/food_court_dashboard.xml",
            "pos_custom_screen/static/src/js/food_court_dashboard.js",

        ],
    },
    # 'assets': {
    #     'web.assets_backend': [
    #         'pos_custom_screen/static/src/js/food_court_dashboard.js',
    #     ],
    #     'web.assets_qweb': [
    #         'pos_custom_screen/static/src/xml/food_court_dashboard.xml',
    #     ],
    # },

}
