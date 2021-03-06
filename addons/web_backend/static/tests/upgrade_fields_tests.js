odoo.define('web_backend.upgrade_fields_tests', function (require) {
"use strict";

/**
 * Upgrade widgets have a specific behavior in community which is overriden
 * in enterprise by the default FieldBoolean and FieldRadio behaviors
 */

var FormView = require('web.FormView');
var testUtils = require('web.test_utils');

var createView = testUtils.createView;

QUnit.module('fields', {}, function () {

QUnit.module('upgrade_fields', {
    beforeEach: function () {
        this.data = {
            partner: {
                fields: {
                    bar: {string: "Bar", type: "boolean"},
                },
            },
        };
    },
}, function () {

    QUnit.module('FieldUpgrade');

    QUnit.test('widget upgrade_boolean in a form view (enterprise version)', function (assert) {
        assert.expect(2);

        var form = createView({
            View: FormView,
            model: 'partner',
            data: this.data,
            arch: '<form>' +
                    '<div class="o_field"><field name="bar" widget="upgrade_boolean"/></div>' +
                    '<div class="o_label"><label for="bar"/><div>Coucou</div></div>' +
                '</form>',
        });

        assert.strictEqual(form.$('.label').length, 0,
            "there should be no upgrade label");
        assert.strictEqual(form.$('.o_label').text(), "BarCoucou",
            "the label should be correct");
        form.destroy();
    });

});
});
});
