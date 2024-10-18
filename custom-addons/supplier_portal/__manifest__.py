{
    "name": "Supplier Portal",
    "author": "Techno THT Gmbh",
    "website": "www.odoomates.tech",
    "summary": "Supplier Portal",
    "depends": ["ship_management", "docking", "portal"],
    "data": [
        "views/home.xml",
        "views/portal_rfq_templates.xml",
        "views/portal_breadcrumbs.xml",
        "views/ship_management/material_paint_quotes.xml",
        "views/ship_management/material_supplier_quote.xml",
        "views/ship_management/paint_supplier_quote.xml",
        "views/ship_management/job_supplier_quote.xml",
        "views/docking/docking_plan.xml",
        "views/docking/material_supplier_quote.xml",
        "views/docking/paint_supplier_quote.xml",
        "views/docking/job_supplier_quote.xml",
        "views/ship_management/fuel_supplier_quote.xml",
    ],
    "application": True,
}
