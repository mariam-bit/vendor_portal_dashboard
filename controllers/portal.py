from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from collections import defaultdict
import json

class VendorPortal(CustomerPortal):

    def _prepare_portal_layout_values(self, **kwargs):
        values = super(VendorPortal, self)._prepare_portal_layout_values(**kwargs)
        values.update({
            'invoice_count': 0,
            'quotation_count': 0,
            'order_count': 0,
            'last_updated': fields.Datetime.now(),
        })
        return values

    @http.route(['/my/orders'], type='http', auth="user", website=True)
    def portal_my_orders(self, categ_id=None, **kw):
        partner = request.env.user.partner_id
        
        all_vendor_products = request.env['product.product'].sudo().search([
            ('seller_ids.partner_id', '=', partner.id)
        ])
        categories = all_vendor_products.mapped('categ_id')

        product_domain = [('seller_ids.partner_id', '=', partner.id)]
        if categ_id:
            product_domain.append(('categ_id', '=', int(categ_id)))
        
        vendor_products = request.env['product.product'].sudo().search(product_domain)

        sales_domain = [
            ('product_id', 'in', vendor_products.ids),
            ('state', 'in', ['sale', 'done'])
        ]
        sales_history = request.env['sale.order.line'].sudo().search(sales_domain, order="create_date desc")

        monthly_dynamics = defaultdict(float)
        product_sales_data = defaultdict(float)
        total_units = 0

        for line in sales_history:
            month = line.create_date.strftime('%B %Y')
            monthly_dynamics[month] += line.product_uom_qty
            product_sales_data[line.product_id.name] += line.product_uom_qty
            total_units += line.product_uom_qty

        # Prepare Top 5 Products Chart
        sorted_products = sorted(product_sales_data.items(), key=lambda x: x[1], reverse=True)[:5]
        chart_data = {
            'labels': [p[0] for p in sorted_products],
            'datasets': [{
                'label': 'Units Sold',
                'data': [p[1] for p in sorted_products],
                'backgroundColor': '#6a1b9a',
                'borderRadius': 6,
            }]
        }

        values = self._prepare_portal_layout_values(**kw)
        values.update({
            'is_vendor': True,
            'vendor_products': vendor_products,
            'categories': categories,
            'current_categ_id': int(categ_id) if categ_id else False,
            'sales_history': sales_history,
            'monthly_sales': dict(monthly_dynamics),
            'total_units_sold': int(total_units),
            'chart_data': json.dumps(chart_data),
            'page_name': 'vendor_sales',
            'last_updated': fields.Datetime.now(),
        })
        
        return request.render("vendor_portal_dashboard.vendor_sales_history_page", values)