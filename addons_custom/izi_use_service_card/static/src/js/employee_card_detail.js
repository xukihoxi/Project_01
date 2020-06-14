odoo.define('izi_use_service_card.widget', function(require) {
"use strict";


var AbstractField = require('web.AbstractField');
var core = require('web.core');
var registry = require('web.field_registry');
var _t = core._t;
var qweb = core.qweb;
var rpc = require('web.rpc');

var ResPartnerCustom = AbstractField.extend({
    custom_events: _.extend({}, AbstractField.prototype.custom_events, {
        'field_changed': '_onFieldChanged',
    }),

    init: function () {
        this._super.apply(this, arguments);
    },

    _render: function () {
        this._super.apply(this, arguments);
        this._rednder_element();
    },

    _rednder_element: function () {
        // var obj = this.getMainObject();
        var self = this;
        var partner_id = this.res_id;
        return rpc.query({
                model: this.model,
                method: 'get_card_detail_customer',
                args: [partner_id],
            }).then(function (res) {
            self.$el.append($(qweb.render("izi_use_service_card.EmployeeCardDetail", {widget: this, items: res})));
        })

    },
    });
registry.add('use_service_detail', ResPartnerCustom);
});

