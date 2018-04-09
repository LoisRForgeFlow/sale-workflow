# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class ChangeProductionQty(models.TransientModel):
    _inherit = "change.production.qty"

    # TODO: assess a field "explode_qty_update"
    # explode_qty_update = fields.Boolean(
    #     string="Explode Qty Modification",
    #     help="If set the change will be exploded through the BoM to MOs that "
    #          "were created from this one (same procurement group) or to new "
    #          "ones."
    # )

    # @api.multi
    # def change_prod_qty(self):
    #     res = super().change_prod_qty()
    #     for rec in self:
    #         if rec.explode_qty_update:
    #             # search
    #             pass
    #     return res