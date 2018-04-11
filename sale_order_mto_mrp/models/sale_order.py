# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        """Do not return the warning asking to manually modify the picking."""
        super()._onchange_product_uom_qty()
        return {}

    @api.multi
    def write(self, values):
        """When a SO line qty is reduced, the reduction is propagated to
        directly related stock moves."""
        lines = False
        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            lines = self.filtered(
                lambda r: r.state == 'sale' and float_compare(
                    r.product_uom_qty, values['product_uom_qty'],
                    precision_digits=precision) == 1)
        if lines:
            for line in lines:
                decrease = line.product_uom_qty - values['product_uom_qty']
                line._decrease_product_uom_qty_actions(decrease)
        return super(SaleOrderLine, self).write(values)

    @api.multi
    def _decrease_product_uom_qty_actions(self, decrease):
        self.ensure_one()
        domain = self._get_domain_moves_to_decrease()
        moves = self.env['stock.move'].search(domain)  # TODO: evaluate: self.mapped('move_ids')
        if moves:
            moves.decrease_product_uom_qty(decrease)
            mo = moves.mapped('move_orig_ids.production_id')
            if mo:
                qty = mo[0].product_qty - decrease  # sure? uom?
                wiz = self.env['change.production.qty'].create({
                    'mo_id': mo[0].id,
                    'product_qty': qty,
                # TODO: add 'explode_qty_update' if implemented.
                })
                wiz.change_prod_qty()
            po_lines = moves.mapped('created_purchase_line_id')  # TODO: Compare with no MTO
            po_lines_filtered = po_lines.filtered(
                lambda l: l.order_id.state in ['draft', 'sent'])  # TODO: assess these states...
            if po_lines_filtered:
                # TODO check that msg is posted on PO.
                # TODO check UoM
                po_lines_filtered[0].product_qty -= decrease
        return True

    @api.multi
    def _get_domain_moves_to_decrease(self):
        domain = [
            ('product_id', '=', self.product_id.id),
            ('origin', '=', self.order_id.name),
            ('state', 'not in', ['done', 'cancel'])
        ]
        return domain
