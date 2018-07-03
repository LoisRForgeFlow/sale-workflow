# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def _get_date_expected_from_so(self, move, new_date, old_date):
        """Extend to consider warehouse calendar"""
        calendar = self.order_id.warehouse_id.calendar_id
        if calendar:
            if new_date > old_date:
                work_delta = sum(1 for i in calendar._iter_work_days(
                    old_date, new_date + timedelta(days=1), None))
            else:
                work_delta = sum(-1 for i in calendar._iter_work_days(
                    new_date, old_date + timedelta(days=1), None))

            date_expected = calendar.plan_days(
                work_delta,
                fields.Datetime.from_string(move.date_expected))
            return date_expected
        return super()._get_date_expected_from_so(move, new_date, old_date)
