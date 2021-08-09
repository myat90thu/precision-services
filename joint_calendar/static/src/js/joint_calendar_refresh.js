odoo.define('joint_calendar.joint_calendar_refresh', function (require) {
"use strict";

var core = require('web.core');
var CalendarRenderer = require('web.CalendarRenderer');
var CalendarController = require('web.CalendarController');

var _t = core._t;

CalendarController.include({
    custom_events: _.extend({}, CalendarController.prototype.custom_events, {
        refreshJointCalendar: '_onRefreshJointCalendar',
    }),
    _onRefreshJointCalendar: function (event) {
        var self = this;
        this._rpc({
            model: "joint.calendar",
            method: "action_generate_events",
            args: [[self.context.default_joint_calendar_id]],
            context: self.context,
        }).then(function (res) {
            self.reload();
        }).then(event.data.on_always, event.data.on_always);
    }
});

CalendarRenderer.include({
    events: _.extend({}, CalendarRenderer.prototype.events, {
        'click .refresh_joint': '_onRefreshJointCalendar',
    }),
    _initSidebar: function () {
        var self = this;
        this._super.apply(this, arguments);
        this.$refreshButton = $();
        if (this.model === "joint.event") {
            this.$refreshButton = $('<button/>', {type: 'button', html: _t("Refresh")})
                                .addClass('refresh_joint oe_button btn btn-secondary')
                                .prepend($('<i/>', {
                                    class: "fa fa-refresh mr4",
                                }))
                                .appendTo(self.$sidebar);
        }
    },
    _onRefreshJointCalendar: function () {
        var self = this;
        var context = this.getSession().user_context;
        this.$refreshButton.prop('disabled', true);
        this.trigger_up('refreshJointCalendar', {
            on_always: function () {
                self.$refreshButton.prop('disabled', false);
            },
        });
    },
});

});
