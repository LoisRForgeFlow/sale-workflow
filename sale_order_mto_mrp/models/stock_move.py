# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "stock.move"

    @api.multi
    def decrease_product_uom_qty(self, decrease):
        for rec in self:
            rec.product_uom_qty -= decrease

    @api.constrains("product_uom_qty")
    def _check_positive_product_uom_qty(self):
        if any([n < 0.0 for n in self.mapped('product_uom_qty')]):
            raise UserError(_(
                "You cannot have a negative qty on a stock.move"))
