# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = "stock.move"

    @api.model
    def _get_new_mo_dates(self, manuf_order, delta):
        """Extend to consider warehouse calendar"""
        mo_date_start, mo_date_end = super()._get_new_mo_dates(
            manuf_order, delta)
        calendar = manuf_order.picking_type_id.warehouse_id.calendar_id
        if calendar:
            mo_date_start = calendar.plan_days(
                -1 * manuf_order.product_id.produce_delay - 1,
                mo_date_end)
        return mo_date_start, mo_date_end
