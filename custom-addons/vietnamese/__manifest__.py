{
    "name": "Vietnamese",
    "author": "Vietnamese",
    "website": "www.vietnamese.tech",
    "summary": "It's Vietnamese",
    "depends": ["mail", "base_automation"],
    "data": [
        "security/role.xml",
        "security/rule.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/menu.xml",
        "views/table.xml",
        "views/ir_ui_menu.xml",
        "views/res_groups.xml",
        "views/ir_model_fields.xml",
        "views/base_automation.xml",
    ],
    "application": True,
    "assets": {
        "web.assets_backend": [
            "vietnamese/static/src/css/**",
            "vietnamese/static/src/js/**",
        ],
    },
}
