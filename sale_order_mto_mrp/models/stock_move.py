# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = "stock.move"

    @api.multi
    def write(self, values):
        # Disable odoo propagation to avoid conflicts.
        self = self.with_context(do_not_propagate=True)
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
        if 'date_expected' in values:
            # if there is a MO directly linked to the next move
            # (MTO SO -> picking (stock move being written now) ->
            # MO (finished products stock moves))
            # we update the MO date accordingly
            # (to update of the stock moves of the MO we rely on
            # mrp.production model, see
            # https://github.com/odoo/odoo/pull/25424)
            if not isinstance(values['date_expected'], datetime):
                new_date = fields.Datetime.from_string(values['date_expected'])
            else:
                new_date = values['date_expected']
            for move in self:
                mos = move.mapped('move_orig_ids.production_id')
                if mos:
                    old_date = fields.Datetime.from_string(move.date_expected)
                    delta = new_date - old_date
                    for mo in mos.with_context(do_not_propagate=True):
                        mo_date_start, mo_date_end = self._get_new_mo_dates(
                            mo, delta)
                        mo.write({
                            'date_planned_start': fields.Datetime.to_string(
                                mo_date_start),
                            'date_planned_finished': fields.Datetime.to_string(
                                mo_date_end),
                        })
        res = super().write(values)
        return res

    @api.model
    def _get_new_mo_dates(self, manuf_order, delta):
        """Allow to modify the way the MO are rescheduled."""
        mo_date_end = fields.Datetime.from_string(
            manuf_order.date_planned_finished) + delta
        mo_date_start = fields.Datetime.from_string(
            manuf_order.date_planned_start) + delta
        return mo_date_start, mo_date_end

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
