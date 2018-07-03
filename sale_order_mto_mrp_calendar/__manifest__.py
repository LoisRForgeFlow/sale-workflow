# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Sale Order MTO MRP Calendar',
    'version': '11.0.1.0.0',
    'summary': "Glue module for sale_order_mto_mrp and mrp_warehouse_calendar",
    'license': 'AGPL-3',
    'author': 'Eficent, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/sale-workflow',
    'category': 'Sale',
    'depends': [
        'sale_order_mto_mrp',
        'mrp_warehouse_calendar',
    ],
    'installable': True,
    'auto_install': True,
}
