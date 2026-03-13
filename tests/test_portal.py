# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged

@tagged('post_install', '-at_install')
class TestVendorPortal(HttpCase):

    def setUp(self):
        super(TestVendorPortal, self).setUp()
        
        # 1. Create the Vendor Partner
        self.vendor_partner = self.env['res.partner'].create({
            'name': 'Test Vendor',
            'email': 'vendor@test.com',
        })

        # 2. Create the Portal User for this Vendor
        self.vendor_user = self.env['res.users'].create({
            'name': 'Vendor User',
            'login': 'vendor_user',
            'password': 'password123',
            'partner_id': self.vendor_partner.id,
            'groups_id': [(4, self.env.ref('base.group_portal').id)],
        })

        # 3. Create a Product assigned to this Vendor
        self.product = self.env['product.product'].create({
            'name': 'Vendor Gadget',
            'type': 'consu',
            'default_code': 'VG-01',
            'seller_ids': [(0, 0, {
                'partner_id': self.vendor_partner.id,
                'min_qty': 1,
                'price': 100,
            })]
        })

        # 4. Create a Sale Order to generate Revenue/Units Sold
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.partner_admin').id, # Customer is Admin
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10,
                'price_unit': 150.0,
            })],
        })
        self.sale_order.action_confirm() # Set state to 'sale'

    def test_01_portal_dashboard_kpis(self):
        """ Test if the layout values (KPIs) are calculated correctly """
        self.authenticate('vendor_user', 'password123')
        
        # Access the inventory details page
        response = self.url_open('/my/inventory-details')
        self.assertEqual(response.status_code, 200)
        
        # Verify the content exists in the rendered HTML (Optional but recommended)
        # We search for the total revenue value (10 units * 150 = 1500)
        self.assertIn('1,500', response.text)
        self.assertIn('Vendor Gadget', response.text)

    def test_02_inventory_chart_data(self):
        """ Test the specific inventory chart route and its JSON data """
        self.authenticate('vendor_user', 'password123')
        
        response = self.url_open('/my/inventory-details')
        self.assertEqual(response.status_code, 200)
        
        # Check if our SKU 'VG-01' appears in the chart labels in the HTML
        self.assertIn('VG-01', response.text)

    def test_03_sales_charts_filtering(self):
        """ Test the charts page with product filters """
        self.authenticate('vendor_user', 'password123')
        
        # Test with a specific product_id filter
        url = '/my/sales-charts?product_id=%s' % self.product.id
        response = self.url_open(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Vendor Gadget', response.text)