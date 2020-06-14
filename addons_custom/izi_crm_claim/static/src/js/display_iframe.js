odoo.define('izi_crm_claim.crm_claim_report', function (require) {
    "use strict";

    var fieldRegistry = require('web.field_registry');
    var DisplayIframe = require('pos_report_birt.DisplayIframe').extend({

    });

    fieldRegistry.add('display_iframe', DisplayIframe);

    return {
        DisplayIframe : DisplayIframe,
    };

});