odoo.define('izi_birt_page.BirtViewerAction', function (require) {
    "use strict";
    var core = require('web.core');
    var Widget = require('web.Widget');
    var BirtPage = Widget.extend({
        template: "BirtPageWidget",
        init: function (parent, options) {
            this.birt_link = options.context.birt_link;
            this.target = options.target;
            if (!this.birt_link) {
                this.birt_link = localStorage['birt_link'] || '404';
            }
            else
                localStorage['birt_link'] = this.birt_link;
            if (options.context.options) {
                this.display_options = options.context.options;
            }
            return this._super(parent, options);
        },
        start: function () {
            this.$el.css({height: '100%', width: '100%', border: 0});

            this.intervalId = setInterval(this.render_options, 100, this);
        },

        /**
         * Render options return from server
         */
        render_options: function (parent) {

            if (parent.target !== 'new') {
                clearInterval(this.intervalId);
                return;
            }
            var modalForm = $('.modal-dialog.modal-lg');
            // check if rendered form
            if(!modalForm.length) {
                return;
            }

            // found it, will clear interval function
            clearInterval(parent.intervalId);

            modalForm.css({
                    transition: 'all .3s linear',
                    height: "100%",
                    width: (parent.display_options && parent.display_options.width) ? parent.display_options.width : "100%",
                    'padding-bottom': "0px"
                });

            modalForm.find('.modal-header').css({
                padding: "8px"
            });
            modalForm.find('.modal-body.oe_act_client').css({
                height: "100%"
            });

            modalForm.find('.modal-content').css({
                height: (parent.display_options && parent.options.height) ? parent.options.height : "100%"
            });

            modalForm.find('.modal-footer').css({
                display: "none"
            });
        }
    });

    core.action_registry.add('BirtViewerAction', BirtPage);
});