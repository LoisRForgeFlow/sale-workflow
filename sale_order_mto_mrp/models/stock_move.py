# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = "stock.move"

    @api.multi
    def write(self, values):
        decreasing_moves = increasing_moves = False
        if 'product_qty' in values:
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            decreasing_moves = self.filtered(
                lambda r: r.state == 'sale' and float_compare(
                    r.product_uom_qty, values['product_uom_qty'],
                    precision_digits=precision) == 1)
            increasing_moves = self.filtered(
                lambda r: r.state == 'sale' and float_compare(
                    r.product_uom_qty, values['product_uom_qty'],
                    precision_digits=precision) == -1)
        if decreasing_moves:
            for move in decreasing_moves:
                decrease = move.product_qty - values['product_uom_qty']
                # domain = self._get_domain_moves_to_decrease()
                # moves = self.env['stock.move'].search(
                #     domain)  # TODO: evaluate: self.mapped('move_ids')
                if move.move_orig_ids:
                    move.move_orig_ids.decrease_product_uom_qty(decrease)
        if increasing_moves:
            for move in increasing_moves:
                increase = values['product_uom_qty'] - move.product_qty
                if move.move_orig_ids:
                    move.move_orig_ids.increase_product_uom_qty(increase)
        res = super().write(values)
        return res

    @api.multi
    def decrease_product_uom_qty(self, decrease):
        for rec in self:
            rec.product_uom_qty -= decrease
        mo = self.mapped('move_orig_ids.production_id')
        if mo:
            qty = mo[0].product_qty - decrease  # sure? uom?
            wiz = self.env['change.production.qty'].create({
                'mo_id': mo[0].id,
                'product_qty': qty,
                # TODO: add 'explode_qty_update' if implemented.
            })
            wiz.change_prod_qty()
        po_lines = self.mapped(
            'created_purchase_line_id')  # TODO: Compare with no MTO
        po_lines_filtered = po_lines.filtered(
            lambda l: l.order_id.state in ['draft',
                                           'sent'])  # TODO: assess these states...
        if po_lines_filtered:
            # TODO check that msg is posted on PO.
            # TODO check UoM
            po_lines_filtered[0].product_qty -= decrease
        return True

    @api.multi
    def increase_product_uom_qty(self, increase):
        # TODO: big issue? merging moves will trigger this...
        pass

    @api.constrains("product_uom_qty")
    def _check_positive_product_uom_qty(self):
        if any([n < 0.0 for n in self.mapped('product_uom_qty')]):
            raise UserError(_(
                "You cannot have a negative qty on a stock.move"))
