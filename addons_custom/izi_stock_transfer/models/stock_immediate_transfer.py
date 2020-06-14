# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError




class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'



    stock_transfer_ids = fields.Many2many('izi.stock.transfer','stock_stransfer_transfer_rel')

    def process_transfer(self):
        for transfer in self.stock_transfer_ids:
            for line in transfer.transfer_line:
                line.quantity_to = line.quantity_from
            if transfer.stock_picking_to.id == False:
                picking_id = transfer._create_picking(transfer.stock_picking_type.id,transfer.dest_location_id.id, transfer.warehouse_id.x_wh_transfer_loc_id.id, False)
                if picking_id.id == False:
                    raise UserError(_("Thông báo"), _("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))
                transfer.update({'stock_picking_to': picking_id.id})
                #Xác nhận picking
                picking_id.action_assign()
                picking_id.button_validate()
            else:
                transfer.stock_picking_to.action_assign()
                transfer.stock_picking_to.button_validate()
            if transfer.stock_picking_to.state == 'done':
                transfer.state = transfer.stock_picking_to.state
        return True