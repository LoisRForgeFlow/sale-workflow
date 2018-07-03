# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo import fields
from odoo.tests.common import SavepointCase


class TestSaleOrderMtoMrpCalendar(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.pt_obj = cls.env['product.template']
        cls.product_obj = cls.env['product.product']
        cls.partner_obj = cls.env['res.partner']
        cls.mo_obj = cls.env['mrp.production']
        cls.bom_obj = cls.env['mrp.bom']
        cls.boml_obj = cls.env['mrp.bom.line']
        cls.change_qty_wiz = cls.env['change.production.qty']
        cls.produce_wiz = cls.env['mrp.product.produce']
        cls.so_obj = cls.env['sale.order']
        cls.sol_obj = cls.env['sale.order.line']
        # WH and routes:
        cls.warehouse = cls.env.ref('stock.warehouse0')
        route_manufacture = cls.warehouse.manufacture_pull_id.route_id.id
        route_buy = cls.env.ref('purchase.route_warehouse0_buy').id
        route_mto_id = cls.warehouse.mto_pull_id.route_id
        route_mto = route_mto_id.id
        # Add 2 days of delay to MTO rules
        route_mto_id.pull_ids.write({'delay': 2})

        # Partners:
        vendor1 = cls.partner_obj.create({'name': 'Vendor 1'})
        customer1 = cls.partner_obj.create({'name': 'Customer 1'})

        # Create products:
        cls.prod_tp1 = cls.product_obj.create({
            'name': 'Test Product 1',
            'type': 'product',
            'list_price': 150.0,
            'produce_delay': 5.0,
            'route_ids': [(6, 0, [route_manufacture, route_mto])],
        })
        cls.prod_ti1 = cls.product_obj.create({
            'name': 'Test Product Intermediate 1',
            'type': 'product',
            'produce_delay': 2.0,
            'route_ids': [(6, 0, [route_manufacture, route_mto])],
        })
        cls.prod_rm1 = cls.product_obj.create({
            'name': 'Test Raw Material 1',
            'type': 'product',
            'route_ids': [(6, 0, [route_buy])],
            'seller_ids': [(0, 0, {'name': vendor1.id, 'price': 10.0})]
        })
        cls.prod_rm2 = cls.product_obj.create({
            'name': 'Test Raw Material 2',
            'type': 'product',
            'route_ids': [(6, 0, [route_buy])],
            'seller_ids': [(0, 0, {'name': vendor1.id, 'price': 20.0})]
        })
        cls.prod_rm3 = cls.product_obj.create({
            'name': 'Test Raw Material 3',
            'type': 'product',
            'route_ids': [(6, 0, [route_buy])],
            'seller_ids': [(0, 0, {'name': vendor1.id, 'price': 30.0})]
        })

        # Create BoMs:
        cls.test_bom_1 = cls.env['mrp.bom'].create({
            'product_id': cls.prod_tp1.id,
            'product_tmpl_id': cls.prod_tp1.product_tmpl_id.id,
            'product_uom_id': cls.prod_tp1.uom_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })
        test_bom_1_l1 = cls.env['mrp.bom.line'].create({
            'bom_id': cls.test_bom_1.id,
            'product_id': cls.prod_rm1.id,
            'product_qty': 1.0,
        })
        test_bom_1_l2 = cls.env['mrp.bom.line'].create({
            'bom_id': cls.test_bom_1.id,
            'product_id': cls.prod_ti1.id,
            'product_qty': 2.0,
        })

        test_bom_2 = cls.env['mrp.bom'].create({
            'product_id': cls.prod_ti1.id,
            'product_tmpl_id': cls.prod_ti1.product_tmpl_id.id,
            'product_uom_id': cls.prod_ti1.uom_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })
        test_bom_2_l1 = cls.env['mrp.bom.line'].create({
            'bom_id': test_bom_2.id,
            'product_id': cls.prod_rm2.id,
            'product_qty': 3.0,
        })
        test_bom_2_l2 = cls.env['mrp.bom.line'].create({
            'bom_id': test_bom_2.id,
            'product_id': cls.prod_rm3.id,
            'product_qty': 1.0,
        })

        # Add calendar to the warehouse:
        calendar = cls.env.ref('resource.resource_calendar_std')
        cls.warehouse.calendar_id = calendar.id

        # Dates:
        base_date = fields.Datetime.from_string('2097-01-07 09:00:00')
        cls.date_1 = fields.Datetime.to_string(
            calendar.plan_days(1+1, base_date))
        cls.date_3 = fields.Datetime.to_string(
            calendar.plan_days(3+1, base_date))
        cls.date_5 = fields.Datetime.to_string(
            calendar.plan_days(5+1, base_date))
        cls.date_8 = fields.Datetime.to_string(
            calendar.plan_days(8+1, base_date))
        cls.date_10 = fields.Datetime.to_string(
            calendar.plan_days(10+1, base_date))
        cls.date_12 = fields.Datetime.to_string(
            calendar.plan_days(12+1, base_date))
        cls.date_17 = fields.Datetime.to_string(
            calendar.plan_days(17+1, base_date))
        cls.date_19 = fields.Datetime.to_string(
            calendar.plan_days(19+1, base_date))

        # Create SO:
        cls.so = cls.so_obj.create({
            'partner_id': customer1.id,
            'partner_invoice_id': customer1.id,
            'partner_shipping_id': customer1.id,
            'order_line': [(0, 0, {
                'name': cls.prod_tp1.name,
                'product_id': cls.prod_tp1.id,
                'product_uom_qty': 50.0,
                'product_uom': cls.prod_tp1.uom_id.id,
                'price_unit': cls.prod_tp1.list_price,
                'requested_date': cls.date_12,
            })],
            'pricelist_id': cls.env.ref('product.list0').id,
        })

    # Depends on https://github.com/odoo/odoo/pull/25424
    def test_01_modify_requested_date_with_calendar(self):
        """Tests if the requested date modification is propagated to the
        already existing MOs considering the warehouse calendar"""
        self.so.action_confirm()
        mos = self.mo_obj.search([('origin', '=', self.so.name)])
        main_mo = mos.filtered(lambda mo: mo.product_id == self.prod_tp1)
        sub_mo = mos.filtered(lambda mo: mo.product_id == self.prod_ti1)
        picking = self.so.picking_ids[0]
        self.assertEqual(picking.scheduled_date, self.date_10)
        self.assertEqual(main_mo.date_planned_start, self.date_5)
        self.assertEqual(main_mo.date_planned_finished, self.date_10)
        self.assertEqual(sub_mo.date_planned_start, self.date_3)
        self.assertEqual(sub_mo.date_planned_finished, self.date_5)
        # Bring forward Requested Date (-2 days):
        self.so.order_line[0].requested_date = self.date_10
        self.assertEqual(picking.scheduled_date, self.date_8)
        self.assertEqual(main_mo.date_planned_start, self.date_3)
        self.assertEqual(main_mo.date_planned_finished, self.date_8)
        self.assertEqual(sub_mo.date_planned_start, self.date_1)
        self.assertEqual(sub_mo.date_planned_finished, self.date_3)
        # Delay Requested Date (+9 days):
        self.so.order_line[0].requested_date = self.date_19
        self.assertEqual(picking.scheduled_date, self.date_17)
        self.assertEqual(main_mo.date_planned_start, self.date_12)
        self.assertEqual(main_mo.date_planned_finished, self.date_17)
        self.assertEqual(sub_mo.date_planned_start, self.date_10)
        self.assertEqual(sub_mo.date_planned_finished, self.date_12)
