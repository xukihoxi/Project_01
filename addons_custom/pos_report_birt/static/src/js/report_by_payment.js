odoo.define('pos_report_birt.report_by_payment', function (require) {
    "use strict";


    var ControlPanelMixin = require('web.ControlPanelMixin');
    var Widget = require('web.Widget');
    var ReportByPayment = Widget.extent(ControlPanelMixin, {
        events: {
            'click #create_report': 'create_report'
        },
        create_report: function(){
            var url = 'https://izisolution.vn'
            $('#iframe_url').attr('src', url);
        }
    });

    //core.action_registry.add('tag_crm_claim_report', ClaimReport);

    return {
        ReportByPayment : ReportByPayment,
    };

});