from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from collections import defaultdict, OrderedDict
import json

class VendorPortal(CustomerPortal):

    def _prepare_portal_layout_values(self, **kwargs):
        """ This method runs for every portal page. 
            We put the KPI data here so it's globally available. """
        values = super(VendorPortal, self)._prepare_portal_layout_values(**kwargs)
        partner = request.env.user.partner_id
        
        all_products = request.env['product.product'].sudo().search([
            ('seller_ids.partner_id', '=', partner.id)
        ])
        
        sales_lines = request.env['sale.order.line'].sudo().search([
            ('product_id', 'in', all_products.ids),
            ('order_id.state', 'in', ['sale', 'done'])
        ])
        total_revenue = sum(sales_lines.mapped('price_subtotal'))
        total_units = sum(sales_lines.mapped('product_uom_qty'))

        low_stock_count = len(all_products.filtered(lambda p: p.qty_available < 5))

        values.update({
            'invoice_count': 0,
            'quotation_count': 0,
            'order_count': 0,
            'last_updated': fields.Datetime.now(),
            'total_revenue': total_revenue,
            'total_units_sold': int(total_units),
            'total_products_count': len(all_products),
            'low_stock_count': low_stock_count,
            'res_company': request.env.company,
        })
        return values

    @http.route(['/my/inventory-details'], type='http', auth="user", website=True)
    def portal_my_inventory_details(self, **kw):
        partner = request.env.user.partner_id
        vendor_products = request.env['product.product'].sudo().search([
            ('seller_ids.partner_id', '=', partner.id)
        ])

        inventory_data = defaultdict(float)
        for prod in vendor_products:
            sku = prod.default_code or 'Unknown'
            inventory_data[sku] += prod.qty_available

        chart_data = {
            'labels': list(inventory_data.keys()),
            'datasets': [{
                'data': list(inventory_data.values()),
                'backgroundColor': ['#6a1b9a', '#9c27b0', '#e1bee7', '#4a148c', '#ba68c8'],
            }]
        }

        values = self._prepare_portal_layout_values(**kw)
        values.update({
            'vendor_products': vendor_products,
            'inventory_chart_data': json.dumps(chart_data),
            'page_name': 'inventory_details',
        })
        return request.render("vendor_portal_dashboard.inventory_details_page", values)

    @http.route(['/my/orders'], type='http', auth="user", website=True)
    def portal_my_orders(self, categ_id=None, **kw):
        partner = request.env.user.partner_id
        current_categ_id = int(categ_id) if categ_id else False

        all_vendor_products = request.env['product.product'].sudo().search([
            ('seller_ids.partner_id', '=', partner.id)
        ])

        product_domain = [('seller_ids.partner_id', '=', partner.id)]
        if current_categ_id:
            product_domain.append(('categ_id', '=', current_categ_id))
        vendor_products = request.env['product.product'].sudo().search(product_domain)

        sales_domain = [
            ('product_id', 'in', all_vendor_products.ids),
            ('order_id.state', 'in', ['sale', 'done']),
        ]
        if current_categ_id:
            sales_domain.append(('product_id.categ_id', '=', current_categ_id))

        sales_history = request.env['sale.order.line'].sudo().search(
            sales_domain, order="create_date desc"
        )

        categories = all_vendor_products.mapped('categ_id')
        monthly_dynamics = defaultdict(float)
    
        for line in sales_history:
            month = line.create_date.strftime('%B %Y')
            monthly_dynamics[month] += line.product_uom_qty

        values = self._prepare_portal_layout_values(**kw)
        values.update({
            'is_vendor': True,
            'vendor_products': vendor_products,
            'categories': categories,
            'current_categ_id': current_categ_id,
            'monthly_sales': dict(monthly_dynamics),
            'page_name': 'vendor_sales',
        })

        return request.render("vendor_portal_dashboard.vendor_sales_history_page", values)
    


    @http.route(['/my/support'], type='http', auth="user", website=True)
    def portal_my_support(self, **kw):
        values = self._prepare_portal_layout_values(**kw)
        values.update({
            'page_name': 'support',
        })
        return request.render("vendor_portal_dashboard.vendor_support_page", values)
    
    def get_protal_data(self,partner_id,product_id):
        current_partner_id = int(partner_id) if partner_id else False
        current_product_id = int(product_id) if product_id else False
        all_vendor_products = request.env['product.product'].sudo().search([
            ('seller_ids.partner_id', '=', partner.id)
        ])

        all_sales_lines = request.env['sale.order.line'].sudo().search([
            ('product_id', 'in', all_vendor_products.ids),
            ('order_id.state', 'in', ['sale', 'done']),
        ], order="create_date asc")

        filtered_domain = [
            ('product_id', 'in', all_vendor_products.ids),
            ('order_id.state', 'in', ['sale', 'done']),
        ]
        if current_partner_id:
            filtered_domain.append(('order_id.partner_id', '=', current_partner_id))
        if current_product_id:
            filtered_domain.append(('product_id', '=', current_product_id))

        sales_history = request.env['sale.order.line'].sudo().search(
            filtered_domain, order="create_date desc"
        )
        return sales_history

    @http.route(['/my/sales-charts'], type='http', auth="user", website=True)
    def portal_sales_charts(self, partner_id=None, product_id=None, **kw):
        partner = request.env.user.partner_id
        current_partner_id = int(partner_id) if partner_id else False
        current_product_id = int(product_id) if product_id else False

        all_vendor_products = request.env['product.product'].sudo().search([
            ('seller_ids.partner_id', '=', partner.id)
        ])

        all_sales_lines = request.env['sale.order.line'].sudo().search([
            ('product_id', 'in', all_vendor_products.ids),
            ('order_id.state', 'in', ['sale', 'done']),
        ], order="create_date asc")

        filtered_domain = [
            ('product_id', 'in', all_vendor_products.ids),
            ('order_id.state', 'in', ['sale', 'done']),
        ]
        if current_partner_id:
            filtered_domain.append(('order_id.partner_id', '=', current_partner_id))
        if current_product_id:
            filtered_domain.append(('product_id', '=', current_product_id))

        sales_history = request.env['sale.order.line'].sudo().search(
            filtered_domain, order="create_date desc"
        )

        monthly = defaultdict(float)
        by_customer = defaultdict(float)
        by_product = defaultdict(float)

        for line in all_sales_lines:
            monthly[line.create_date.strftime('%B %Y')] += line.product_uom_qty
            by_customer[line.order_id.partner_id.name] += line.product_uom_qty
            by_product[line.product_id.name] += line.product_uom_qty

        monthly_chart_data = json.dumps({
            'labels': list(monthly.keys()),
            'data': list(monthly.values()),
        })
        customer_chart_data = json.dumps({
            'labels': list(by_customer.keys()),
            'datasets': [{'data': list(by_customer.values()), 'backgroundColor': []}]
        })
        top_products = sorted(by_product.items(), key=lambda x: x[1], reverse=True)[:5]
        product_chart_data = json.dumps({
            'labels': [p[0] for p in top_products],
            'data': [p[1] for p in top_products],
        })

        customer_order_counts = {}
        for line in all_sales_lines:
            cust = line.order_id.partner_id
            if cust.id not in customer_order_counts:
                customer_order_counts[cust.id] = {
                    'id': cust.id,
                    'name': cust.name,
                    'orders': set(),
                }
            customer_order_counts[cust.id]['orders'].add(line.order_id.id)

        customers = sorted([
            {
                'id': v['id'],
                'name': v['name'],
                'display_name': '%s (%d)' % (v['name'], len(v['orders'])),
            }
            for v in customer_order_counts.values()
        ], key=lambda x: x['name'])

        groups = OrderedDict()
        for line in sales_history:
            pid = line.order_id.partner_id.id
            if pid not in groups:
                groups[pid] = {
                    'partner_id': pid,
                    'partner_name': line.order_id.partner_id.name,
                    'lines': [],
                    'order_count': 0,
                    'total_qty': 0,
                    'total_amount': 0.0,
                    'order_ids': set(),
                }
            groups[pid]['lines'].append(line)
            groups[pid]['order_ids'].add(line.order_id.id)
            groups[pid]['total_qty'] += int(line.product_uom_qty)
            groups[pid]['total_amount'] += line.price_subtotal

        for g in groups.values():
            g['order_count'] = len(g['order_ids'])
            del g['order_ids']

        values = self._prepare_portal_layout_values(**kw)
        values.update({
            'monthly_chart_data': monthly_chart_data,
            'customer_chart_data': customer_chart_data,
            'product_chart_data': product_chart_data,
            'grouped_sales': list(groups.values()),
            'customers': customers,
            'filter_products': all_vendor_products,
            'current_partner_id': current_partner_id,
            'current_product_id': current_product_id,
            'page_name': 'vendor_charts',
        })
        return request.render("vendor_portal_dashboard.vendor_sales_charts_page", values)

