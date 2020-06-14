odoo.define('pos_report_birt.DisplayIframe', function(require){
"use strict";

    var relationFields = require('web.relational_fields');
    var fieldRegistry = require('web.field_registry');
    var rpc = require("web.rpc");

    var DisplayIframe = relationFields.FieldReference.extend({});

    fieldRegistry.add('display_iframe', DisplayIframe);

    return DisplayIframe;

});