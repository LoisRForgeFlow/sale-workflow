# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _existing_mo_get_domain(self, product_id, values):
        # TODO:bom_id? product_id?
        domain = ()
        gpo = self.group_propagation_option
        group = (gpo == 'fixed' and self.group_id) or \
                (gpo == 'propagate' and values['group_id']) or False

        domain += (
            ('product_id', '=', product_id.id),
            ('state', 'not in', ['cancel', 'done']),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('company_id', '=', values['company_id'].id),
            )
        if group:
            domain += (('procurement_group_id', '=', group.id),)
        return domain

    @api.multi
    def _run_manufacture(self, product_id, product_qty, product_uom,
                         location_id, name, origin, values):
        domain = self._existing_mo_get_domain(product_id, values)
        mo = self.env['mrp.production'].search([dom for dom in domain])
        if not mo:
            return super(ProcurementRule, self)._run_manufacture(
                product_id, product_qty, product_uom,
                location_id, name, origin, values)
        # TODO: do magic. use change.production.qty
        qty = mo[0].product_qty + product_qty  # sure? uom?
        wiz = self.env['change.production.qty'].create({
            'mo_id': mo[0].id,
            'product_qty': qty,  # TODO: add 'explode_qty_update' if implemented.
        })
        wiz.change_prod_qty()


# TODO: reduce qty from SO