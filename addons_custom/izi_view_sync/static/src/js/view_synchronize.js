odoo.define('izi.ViewSync', function (require) {
    var bus = require('bus.bus').bus;
    var WebClient = require('web.WebClient');

    WebClient.include({
        init: function () {
            this._super.apply(this, arguments);
            this.viewSyncChannel = odoo.session_info.db + "izi.view_synchronize";
            bus.add_channel(this.viewSyncChannel);
            bus.on("notification", this, this.on_handler_view_sync);
        },
        on_handler_view_sync: function (notifications) {
            var self = this;
            notifications.forEach(function (notification) {
                if (typeof notification[0] === 'string' && notification[0] === self.viewSyncChannel) {
                    var data = notification[1];
                    var current_state = self._current_state;
                    if (current_state && current_state.model === data.model) {
                        var controller = self.action_manager.inner_widget.views[current_state.view_type].controller;
                        if (controller) {
                            if(controller.mode === 'edit') {
                                return;
                            }
                            if (data.type && data.type.split(',').includes(current_state.view_type)) {
                                if (controller) {
                                    if (data.id && current_state.view_type === 'form' && data.id != current_state.id) {
                                        return;
                                    }
                                    controller.reload();
                                }
                            }
                            // using data.id == current_state.id to compare int = string
                            else if (data.id && current_state.view_type === 'form' && data.id == current_state.id) {
                                controller.reload();
                            } // else no match condition
                        } // ELSE No match condition
                    }
                }
            });
        }
    });
});