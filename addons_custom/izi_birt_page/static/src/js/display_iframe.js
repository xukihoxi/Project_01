odoo.define('pos_report_birt.DisplayIframe', function(require){
"use strict";

    var relationFields = require('web.relational_fields');
    var fieldRegistry = require('web.field_registry');
    var rpc = require("web.rpc");

    var DisplayIframe = relationFields.FieldReference.extend({
        template: 'DisplayIframe',
        init: function (parent, name, record, options) {
            this._super(parent, name, record, options);
            this._model = record.fields[name].relation;
            this._res_id = record.data[name].res_id;
            this.url_report = record.data.url_report;
        },
    });

    fieldRegistry.add('display_iframe', DisplayIframe);

    return DisplayIframe;

});