# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestSaleOrderMto(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_obj = cls.env['product.product']
        cls.partner_obj = cls.env['res.partner']
        cls.so_obj = cls.env['sale.order']
        cls.sol_obj = cls.env['sale.order.line']
        cls.po_obj = cls.env['purchase.order']
        # WH and routes:
        cls.warehouse = cls.env.ref('stock.warehouse0')
        route_mto = cls.warehouse.mto_pull_id.route_id.id
        route_buy = cls.env.ref('purchase.route_warehouse0_buy').id
        # Partners:
        vendor1 = cls.partner_obj.create({'name': 'Vendor 1'})
        customer1 = cls.partner_obj.create({'name': 'Customer 1'})

        # Create products:
        cls.prod_tp1 = cls.product_obj.create({
            'name': 'Test Product 1',
            'type': 'product',
            'list_price': 150.0,
            'produce_delay': 5.0,
            'route_ids': [(6, 0, [route_buy, route_mto])],
            'seller_ids': [(0, 0, {'name': vendor1.id, 'price': 20.0})],
        })

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
                'price_unit': cls.prod_tp1.list_price})],
            'pricelist_id': cls.env.ref('product.list0').id,
        })

    def test_01_increase_so_qty(self):
        """Test to increase the SO line quantity and the impact on
        related Pickings.
        """
        self.so.action_confirm()
        self.assertEqual(len(self.so.mapped('picking_ids.move_lines')), 1)
        prev_qty = self.so.picking_ids.move_lines.product_uom_qty
        self.assertEqual(prev_qty, 50.0)
        self.so.order_line.write({'product_uom_qty': 75.0})
        new_qty = self.so.picking_ids.move_lines.product_uom_qty
        self.assertEqual(new_qty, 75.0)

    def test_02_decrease_so_qty(self):
        """Test to decrease the SO line quantity and the impact on
        related Pickings.
        """
        self.so.action_confirm()
        self.assertEqual(len(self.so.mapped('picking_ids.move_lines')), 1)
        prev_qty = self.so.picking_ids.move_lines.product_uom_qty
        self.assertEqual(prev_qty, 50.0)
        self.so.order_line.write({'product_uom_qty': 30.0})
        new_qty = self.so.picking_ids.move_lines.product_uom_qty
        self.assertEqual(new_qty, 30.0)
        # test that the decrease propagated to PO line.
        po = self.po_obj.search([('origin', 'ilike', self.so.name)])
        po_line = po.order_line.filtered(
            lambda l: l.product_id == self.prod_tp1)
        self.assertEqual(po_line.product_qty, 30.0)

    # TODO: cancel SO delete PO lines?
