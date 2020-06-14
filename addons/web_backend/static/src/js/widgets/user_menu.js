odoo.define('web_backend.UserMenu', function (require) {
"use strict";

/**
 * This file includes the UserMenu widget defined in Community to add or
 * override actions only available in Enterprise.
 */

var config = require('web.config');
var core = require('web.core');
var Dialog = require('web.Dialog');
var UserMenu = require('web.UserMenu');

var _t = core._t;
var QWeb = core.qweb;

UserMenu.include({
    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        if (config.device.isMobile) {
            this.className = 'o_user_menu_mobile';
            this.tagName = 'ul';
            this.template = undefined;
        }
    },
    /**
     * @override
     */
    start: function () {
        if (config.device.isMobile) {
            this.$el.append(QWeb.render('UserMenu.Actions'));
        }
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _onMenuSupport: function () {
        window.open('https://www.odoo.com/help', '_blank');
    },
    /**
     * @private
     */
    _onMenuShortcuts: function() {
        new Dialog(this, {
            size: 'large',
            dialogClass: 'o_act_window',
            title: _t("Keyboard Shortcuts"),
            $content: $(QWeb.render("UserMenu.shortcuts"))
        }).open();
    },
});

});
