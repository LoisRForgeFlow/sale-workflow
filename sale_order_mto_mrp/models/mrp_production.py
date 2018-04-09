# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # TODO: assess a field "explode_qty_update"

    # TODO: post a msg on qty update?

    # TODO: UoM review.

    @api.multi
    def _update_raw_move(self, bom_line, line_data):
        # TODO if to explode do it else return super:
        move = self.move_raw_ids.filtered(
            lambda x: x.bom_line_id.id == bom_line.id and x.state not in (
            'done', 'cancel'))
        prev_qty = move[0].product_uom_qty  # TODO: or product_qty??
        res = super(MrpProduction, self)._update_raw_move(bom_line, line_data)
        new_qty = res.product_uom_qty
        delta = new_qty - prev_qty  # TODO: check negative deltas.
        if res.move_orig_ids and res.move_orig_ids[0].production_id: # TODO: improvement?
            values = res._prepare_procurement_values()
            origin = (move.group_id and move.group_id.name or (
                move.rule_id and move.rule_id.name or move.origin or
                move.picking_id.name or "/"))
            self.env["procurement.group"].run(
                move.product_id, delta, move.product_uom, move.location_id,
                move.rule_id and move.rule_id.name or "/", origin, values)
                # product_id, product_qty, product_uom, location_id,
                # name, origin, values)
        return res
