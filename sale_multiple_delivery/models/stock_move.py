# -*- coding: utf-8 -*-

from odoo import models
from odoo.tools.float_utils import float_compare
from odoo.tools.misc import groupby


class StockMove(models.Model):
    """ inherits stock_move to manage pickings with respect to the
        products in the order line """

    _inherit = "stock.move"

    def _assign_picking(self):
        """ Extending _assign_picking function to create new pickings for
        order lines having different products. """

        picking_obj = self.env['stock.picking']
        grouped_moves = groupby(self, key=lambda m: m._key_assign_picking())
        for group, moves in grouped_moves:
            moves = self.env['stock.move'].concat(*moves)
            picking = moves[0]._search_picking_for_assignation()
            if picking:
                vals = {}
                if any(picking.partner_id.id != move.partner_id.id for move in moves):
                    vals['partner_id'] = False
                if any(picking.origin != move.origin for move in moves):
                    vals['origin'] = False
                if vals:
                    picking.write(vals)
            else:
                moves = moves.filtered(
                    lambda m: float_compare(
                        m.product_uom_qty, 0.0,
                        precision_rounding=m.product_uom.rounding) >= 0)
                if not moves:
                    continue
                products = moves.mapped('product_id')
                if len(products) <= 1:
                    return super(StockMove, self)._assign_picking()
                else:
                    # If there's multiple products, multiple pickings
                    for product in products:
                        product_moves = moves.filtered(lambda m: m.product_id == product)
                        picking_vals = product_moves[0]._get_new_picking_values()
                        new_picking = picking_obj.create(picking_vals)
                        product_moves.write({'picking_id': new_picking.id})
        return True
