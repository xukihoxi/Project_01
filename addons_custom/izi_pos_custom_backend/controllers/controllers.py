# -*- coding: utf-8 -*-
from odoo import http
from suds.client import Client
import logging
import json
from datetime import datetime
import logging
import requests

_logger = logging.getLogger(__name__)

class JobCustom(http.Controller):
    @http.route('/test_send_sms/', auth='public')
    def sangla_test_send_sms(self, **kw):
        BULK_API_URL = "http://103.68.240.146:8018/VMGAPI.asmx"
        test = "http://203.190.170.43:8998/bulkapi?wsdl"
        OPTION = 0

        # bulkSMS = Client(BULK_API_URL)
        test = Client(test)
        msg_reponse = test.service.BulkSendSms('84963270363','Lavener', 'Hello Sang', '', 'user', 'password')
        return str(msg_reponse)
