odoo.define('ks_dashboard_ninja_list.ks_dashboard_ninja_list_view_preview', function (require) {
    "use strict";

    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_utils = require('web.field_utils');

    var QWeb = core.qweb;

    var KsListViewPreview = AbstractField.extend({
        supportedFieldTypes: ['char'],

        resetOnAnyFieldChange: true,

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.state = {};
        },

        _render: function () {
            this.$el.empty()
            if (this.recordData.ks_dashboard_item_type === 'ks_list_view') {
                if(this.recordData.ks_list_view_type ===  'ungrouped'){
                    if (this.recordData.ks_list_view_fields.count !== 0) {
                        this.ksRenderListView()
                    } else {
                        this.$el.append($('<div>').text("Select Fields to show in list view."));

                    }
                } else if(this.recordData.ks_list_view_type ===  'grouped'){
                    if(this.recordData.ks_chart_relation_groupby && this.recordData.ks_list_view_group_fields.count !== 0){
                        this.ksRenderListView()
                    }else {
                        this.$el.append($('<div>').text("Select Fields and Group By to show in list view"));
                    }
                }
            }
        },

        ksRenderListView: function () {
            var field = this.recordData;
            var ks_list_view_name;
            if (field.name) ks_list_view_name = field.name;
            else if (field.ks_model_name) ks_list_view_name = field.ks_model_id.data.display_name;
            else ks_list_view_name = "Name";

            var list_view_data;
            if (field.ks_list_view_data) list_view_data = JSON.parse(field.ks_list_view_data);
            else list_view_data = false;

            if(list_view_data){
                for (var i = 0; i < list_view_data.data_rows.length; i++){
                    for (var j = 0; j < list_view_data.data_rows[0]["data"].length; j++){
                        if(typeof(list_view_data.data_rows[i].data[j]) === "number" || list_view_data.data_rows[i].data[j]){
                            if(typeof(list_view_data.data_rows[i].data[j]) === "number"){
                                list_view_data.data_rows[i].data[j]  = field_utils.format.float(list_view_data.data_rows[i].data[j], Float64Array)
                            }
                        } else {
                            list_view_data.data_rows[i].data[j] = "";
                        }
                    }
                }
            }

            if(this.recordData.ks_list_view_type === "ungrouped" && list_view_data){
                var index_data = list_view_data.date_index;
                for (var i = 0; i < index_data.length; i++){
                    for (var j = 0; j < list_view_data.data_rows.length; j++){
                        var index = index_data[i]
                        var date = list_view_data.data_rows[j]["data"][index]
                        if (date) list_view_data.data_rows[j]["data"][index] = field_utils.format.datetime(moment(moment(date).utc(true)._d), {}, {timezone: false});
                        else list_view_data.data_rows[j]["data"][index] = "";
                    }
                }
            }

            var $listViewContainer = $(QWeb.render('ks_list_view_container', {
                ks_list_view_name: ks_list_view_name,
                list_view_data: list_view_data
            }));
            this.$el.append($listViewContainer);

        },

    });
    registry.add('ks_dashboard_list_view_preview', KsListViewPreview);

    return {
        KsListViewPreview: KsListViewPreview,
    };

});