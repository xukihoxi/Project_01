# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

STATE_SELECTOR = [('free', 'Free'), ('busy', 'Busy')]


class CrmTeamBed(models.Model):
    _inherit = 'pos.service.bed'



    def get_bed_state(self, bed_id, time_from, time_to, except_booking_id=None):
        query = '''SELECT sb.id FROM service_booking sb
                    INNER JOIN pos_service_bed_service_booking_rel ctbr ON sb.id = ctbr.service_booking_id
                    WHERE ctbr.pos_service_bed_id = %s and sb.state != 'cancel' 
                    AND ((sb.time_from >= %s AND sb.time_from <= %s) 
                        OR (sb.time_to >= %s AND sb.time_to <= %s) 
                        OR (sb.time_from <= %s AND sb.time_to >= %s))'''
        query_params = [bed_id, time_from, time_to, time_from, time_to, time_from, time_to]
        if except_booking_id:
            query += ''' AND sb.id != %s'''
            query_params += [except_booking_id]
        self._cr.execute(query, tuple(query_params))
        row = self._cr.dictfetchone()
        if row:
            return 'busy'
        return 'free'
