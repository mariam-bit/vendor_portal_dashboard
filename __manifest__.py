{
    'name': 'Vendor Portal Dashboard',
    'version': '1.0',
    'depends': ['base', 'portal', 'sale', 'purchase'],  # Make sure 'sale' is here!
    'data': [
        'data/test_vendor.xml',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
}