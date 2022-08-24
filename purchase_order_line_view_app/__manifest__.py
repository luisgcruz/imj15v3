# -*- coding: utf-8 -*-

{
    'name' : 'Purchase Order Line View',
    "author": "Edge Technologies",
    "version" : "13.0.1.0",
    'live_test_url':'https://youtu.be/ldv6hcqlIeY',
    "images":["static/description/main_screenshot.png"],
    'summary' : 'View for Purchase order line views purchase order lines view purchase order line kanban view for all purchase bill line view PO line view purchase line view purchase line Graph view purchase Line Chart view purchase line Pie Chart view Bar Chart view',
    'description' : """
            purchase order line view for purchse orders.

    """,
    'depends' : ['purchase'],
    "license" : "OPL-1",
    'data' : [
        'security/purchase_order_line_group.xml',
        'views/purchse_order_line.xml',
    ],
    "auto_install": False,
    "installable": True,
    "price": 7,
    "currency": 'EUR',
    'category': 'Purchase',
    
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:






