# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_cancel(self):
        """Find Production Orders linked to the moves that are going to
        be cancel and cancel them too if not started."""
        mos = self.mapped('move_lines.move_orig_ids.production_id')
        res = super(StockPicking, self).action_cancel()
        mos_to_cancel = mos.filtered(
            lambda r: r.state in ['confirmed', 'planned'])  # TODO: handle in progress MOs?
        if mos_to_cancel:
            mos_to_cancel.action_cancel()
        return res
