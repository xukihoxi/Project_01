odoo.define('partner_file.widget', function(require) {
"use strict";

var core = require('web.core');
var AbstractField = require('web.AbstractField');
var basicFields = require('web.basic_fields');
var registry = require('web.field_registry');

var qweb = core.qweb;
var limit_enter_press = false;
var FieldCustomerFiles = basicFields.FieldChar.extend({
    _renderReadonly: function (){
        var images = $.parseJSON(this.recordData.images);
        this.$el.append($(qweb.render("FieldCustomerFiles", {widget: this, items: images})));
    },
});

registry.add('customer_files', FieldCustomerFiles);

});
