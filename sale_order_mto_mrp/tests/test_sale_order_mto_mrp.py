# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestSaleOrderMtoMrp(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.pt_obj = cls.env['product.template']
        cls.product_obj = cls.env['product.product']
        cls.partner_obj = cls.env['res.partner']
        cls.mo_obj = cls.env['mrp.production']
        cls.bom_obj = cls.env['mrp.bom']
        cls.boml_obj = cls.env['mrp.bom.line']
        cls.so_obj = cls.env['sale.order']
        cls.sol_obj = cls.env['sale.order.line']
        # WH and routes:
        cls.warehouse = cls.env.ref('stock.warehouse0')
        route_manufacture = cls.warehouse.manufacture_pull_id.route_id.id
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
        related MOs.
        """
        self.so.action_confirm()
        mos = self.mo_obj.search([('origin', '=', self.so.name)])
        self.assertEqual(len(mos), 2)
        main_mo = mos.filtered(lambda mo: mo.product_id == self.prod_tp1)
        self.assertEqual(main_mo.product_qty, 50.0)
        sub_mo = mos.filtered(lambda mo: mo.product_id == self.prod_ti1)
        self.assertEqual(sub_mo.product_qty, 100.0)
        self.so.order_line.write({'product_uom_qty': 75.0})
        # No new MO should've been created and the qty of the existing ones
        # should've been updated
        mos = self.mo_obj.search([('origin', '=', self.so.name)])
        self.assertEqual(len(mos), 2)
        self.assertEqual(main_mo.product_qty, 75.0)
        self.assertEqual(sub_mo.product_qty, 150.0)

    def test_02_decrease_so_qty(self):
        """Test to decrease the SO line quantity and the impact on
        related MOs.
        """
        self.so.action_confirm()
        mos = self.mo_obj.search([('origin', '=', self.so.name)])
        self.assertEqual(len(mos), 2)
        main_mo = mos.filtered(lambda mo: mo.product_id == self.prod_tp1)
        self.assertEqual(main_mo.product_qty, 50.0)
        sub_mo = mos.filtered(lambda mo: mo.product_id == self.prod_ti1)
        self.assertEqual(sub_mo.product_qty, 100.0)
        self.so.order_line.write({'product_uom_qty': 25.0})
        # No new MO should've been created and the qty of the existing ones
        # should've been updated
        mos = self.mo_obj.search([('origin', '=', self.so.name)])
        self.assertEqual(len(mos), 2)
        self.assertEqual(main_mo.product_qty, 25.0)
        self.assertEqual(sub_mo.product_qty, 50.0)

    def test_03_standalone_mo_update(self):
        """Test to update qty on a standalone MO."""
        main_mo = self.mo_obj.create({
            'product_id': self.prod_tp1.id,
            'product_qty': 15.0,
            'product_uom_id': self.prod_tp1.uom_id.id,
            'bom_id': self.test_bom_1.id,
        })
        sub_mo = self.mo_obj.search([('origin', '=', main_mo.name)])
        self.assertEqual(main_mo.product_qty, 15.0)
        self.assertEqual(sub_mo.product_qty, 30.0)
        # increase qty:
        wiz = self.env['change.production.qty'].create({
            'mo_id': main_mo.id,
            'product_qty': 25.0,
        })
        wiz.change_prod_qty()
        self.assertEqual(main_mo.product_qty, 25.0)
        self.assertEqual(sub_mo.product_qty, 50.0)
        # decrease qty:
        wiz = self.env['change.production.qty'].create({
            'mo_id': main_mo.id,
            'product_qty': 10.0,
        })
        wiz.change_prod_qty()
        self.assertEqual(main_mo.product_qty, 10.0)
        self.assertEqual(sub_mo.product_qty, 20.0)

    def test_04_reducing_main_mo_with_sub_mo_done(self):
        """Tests ..."""
        pass
