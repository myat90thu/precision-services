# -*- coding: utf-8 -*-

import itertools
import logging

from collections import defaultdict

from odoo import _, api, fields, models

from odoo.addons.calendar.models.calendar import get_real_ids
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class joint_event(models.Model):
    """
    The key model to show on the joint calendar interface
    """
    _name = "joint.event"
    _inherit = ["mail.thread"]
    _description = "Joint Event"

    @api.model
    def _selection_res_reference(self):
        """
        The method to return all available models which might be used to be joined
        """
        self._cr.execute("SELECT model, name FROM ir_model ORDER BY name")
        return self._cr.fetchall()

    @api.model
    def _default_res_model(self):
        """
        Default method for res_model
        """
        return self.env['ir.model'].search([('model', '=', 'joint.event')], limit=1)

    @api.model
    def _default_action(self):
        """
        Default method for action

        To-do:
         * does self.res_model_domain makes any sense in default? It does not have an ID
        """
        action = False
        try:
            action = self.env.ref('joint_calendar.joint_event_action')
        except:
            action = self.env['ir.actions.act_window'].search([('res_model', '=', self.res_model_domain)], limit=1)
        return action

    @api.depends('res_id', 'res_model')
    def _compute_res_reference(self):
        """
        Compute method for res_reference

        We need a real id of a parent object (in case of virtual id we get to the parent one)
        """
        for event in self:
            res_reference = False
            if event.res_model_domain and event.res_id_int:
                res_reference = '{},{}'.format(event.res_model_domain, event.res_id_int)
            event.res_reference = res_reference

    @api.depends("res_id")
    def _compute_res_id_int(self):
        """
        Compute method for res_id_int
        We do not keep res id in int due to virtual ids of recurrent calendar events

        Methods:
         * get_real_ids (look at the 'calendar' module)
        """
        for event in self:
            try:
                event.res_id_int = int(event.res_id)
            except:
                try:
                    event.res_id_int = get_real_ids(event.res_id)
                except:
                    _logger.warning("Res id {} can't be converted to int".format(event.res_id))
                    event.res_id_int = False

    @api.depends("attendee")
    def _compute_access_user_ids(self):
        """
        Compute method for access_user_ids
        """
        for event in self:
            event.access_user_ids = event.attendee.mapped("user_ids")

    def _inverse_event_properties(self):
        """
        Inverse method for all event properties: Change parent object, when event is modified
        """
        for event in self:
            try:
                int(event.res_id)
            except:
                _logger.debug("Recurrent events can't be changed in joint events {}".format(event.res_id))
                return True
            if event.res_reference and event.rule_id and event.res_reference._name != self._name:
                item = event.res_reference
                rule = event.rule_id
                data = {}
                if rule.field_start and not rule.field_start.readonly:
                    old_datetime = False
                    if item[rule.field_start.name]:
                        old_datetime = fields.Datetime.from_string(item[rule.field_start.name])
                    new_datetime = False
                    if event.date_start:
                        new_datetime = fields.Datetime.from_string(event.date_start)
                    if old_datetime != new_datetime:
                        data.update({rule.field_start.name: event.date_start,})
                if rule.field_stop and not rule.field_stop.readonly:
                    old_datetime = False
                    if item[rule.field_stop.name]:
                        old_datetime = fields.Datetime.from_string(item[rule.field_stop.name])
                    new_datetime = False
                    if event.date_stop:
                        new_datetime = fields.Datetime.from_string(event.date_stop)
                    if old_datetime != new_datetime:
                        data.update({rule.field_stop.name: event.date_stop,})
                if rule.field_delay \
                        and not rule.field_delay.readonly \
                        and (item[rule.field_delay.name] != event.date_delay):
                    data.update({rule.field_delay.name: event.date_delay,})
                if not rule.always_all_day \
                        and rule.field_all_day \
                        and item[rule.field_start.name] \
                        and item[rule.field_stop.name] \
                        and not rule.field_all_day.readonly \
                        and (item[rule.field_all_day.name] != event.all_day):
                    data.update({rule.field_all_day.name: event.all_day,})
                if rule.field_name and not rule.field_name.readonly and (item[rule.field_name.name] != event.name):
                    data.update({rule.field_name.name: event.name,})
                if rule.field_description \
                        and not rule.field_description.readonly \
                        and (item[rule.field_description.name] != event.description):
                    data.update({rule.field_description.name: event.description,})
                if rule.fields_extra_partner_id \
                        and not rule.fields_extra_partner_id.readonly \
                        and (item[rule.fields_extra_partner_id.name] != event.partner_id):
                    data.update({
                        rule.fields_extra_partner_id.name: event.partner_id.id,
                    })
                if data:
                    item.sudo().write(data)

    def _inverse_res_model(self):
        """
        Inverse method for res_model
        """
        for event in self:
            if event.res_model:
                event.res_model_domain = event.res_model.model
                event.color_model = event.res_model.id
            else:
                event.res_model_domain = 'joint.event'
                event.color_model = 1

    def _inverse_res_reference(self):
        """
        Inverse method for res_reference
        """
        for event in self:
            try:
                int(event.res_id)
                if event.res_reference:
                    values = {
                        'res_model_domain': event.res_reference._model._model,
                        'res_id': str(event.res_reference.id),
                    }
                else:
                    values = {
                        'res_model_domain': False,
                        'res_id': False,
                    }  
            except:
                values = {
                    'res_model_domain': False,
                    'res_id': False,
                }
            event.write(values)

    name = fields.Char(
        string='Title', 
        required=True,
    )
    res_id = fields.Char(string='Related Object ID')
    res_id_int = fields.Integer(
        string="Computed res id",
        compute=_compute_res_id_int,
        store=True,
    )
    res_model = fields.Many2one(
        'ir.model',
        string='Model',
        default=_default_res_model,
        inverse=_inverse_res_model,
        required=True,
        ondelete="cascade",
    )
    color_model = fields.Integer(string='Color', default=1)
    action = fields.Many2one(
        'ir.actions.act_window',
        string='Action',
        domain="[('res_model', '=', res_model_domain)]",
        required=True,
        default=_default_action,
        help='Which form view to open when clicking on an event card',
    )
    res_model_domain = fields.Char(
        string='Tech Domain',
        default='joint.event',
        required=True,
    )
    joint_calendar_id = fields.Many2one(
        'joint.calendar',
        string='Joint Calendar',
        ondelete="cascade",
    )
    rule_id = fields.Many2one(
        'event.rule',
        string='Rule',
        help='The rule, which makes this event happen',
        ondelete="cascade",
    )
    date_start = fields.Datetime(
        string='Start',
        inverse=_inverse_event_properties,
    )
    date_stop = fields.Datetime(
        string='End',
        inverse=_inverse_event_properties,
    )
    date_delay = fields.Float(
        string='Delay',
        inverse=_inverse_event_properties,
    )
    all_day = fields.Boolean(
        string='Whole Day',
        inverse=_inverse_event_properties,
    )
    attendee = fields.Many2many(
        'res.partner',
        'calendar_event_res_partner_rel_sp',
        'joint_even_rel',
        'part_rel',
        string='Attendees',
        default=lambda self: self.env.user.partner_id,
    )
    access_user_ids = fields.Many2many(
        "res.users",
        "res_user_joint_event_rel_table",
        "res_user_rel_id",
        "joint_event_rel_id",
        compute=_compute_access_user_ids,
        compute_sudo=True,
        store=True,
    )
    description = fields.Html(
        string='Description',
        inverse=_inverse_event_properties,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact", 
        inverse=_inverse_event_properties,            
    )
    res_reference = fields.Reference(
        selection='_selection_res_reference',
        string='Parent Object',
        compute=_compute_res_reference,
        inverse=_inverse_res_reference,
    )
    alarm_ids = fields.Many2many(
        'calendar.alarm',
        'calendar_alarm_joint_event_rel_sp',
        'joint_event_rel',
        'alarm_rel',
        string='Alarms',
    )
    privacy = fields.Selection(
        [
            ('public', 'Public'), 
            ('private', 'Private')
        ],
        string='Privacy',
        required=True,
        default='public',
        help="""
            * Public - a joint event would be visible for everybody
            * Private - a joint event would be visible only for attendees
        """,
    )

    @api.model
    def check(self, mode, values=None):
        """
        The method to check rights for joint events
        The rights to joint event are the same as for the parent object.
        The logic is taken for the same mechanics for ir.attachment
        """
        if self.env.is_superuser():
            return True
        if not (self.env.is_admin() or self.env.user.has_group('base.group_user')):
            raise AccessError(_("Sorry, you are not allowed to access this document."))


        model_ids = defaultdict(set)          
        require_employee = False
        if self:
            self.env['joint.event'].flush(['res_model_domain', 'res_id_int'])
            self._cr.execute('SELECT res_model_domain, res_id_int FROM joint_event WHERE id IN %s', [tuple(self.ids)])
            
            for res_model_domain, res_id_int in self._cr.fetchall():
                if not res_model_domain:
                    require_employee = True
                    continue
                model_ids[res_model_domain].add(res_id_int)
        
        if values and values.get('res_model_domain') and values.get('res_id_int'):
            model_ids[values['res_model_domain']].add(values['res_id_int'])

        for res_model, res_ids in model_ids.items():
            if res_model not in self.env:
                require_employee = True
                continue
            elif res_model == 'res.users' and len(res_ids) == 1 and self._uid == list(res_ids)[0]:
                continue
            records = self.env[res_model].browse(res_ids).exists()
            if len(records) < len(res_ids):
                require_employee = True
            
            access_mode = 'write' if mode in ('create', 'unlink') else mode
            records.check_access_rights(access_mode)
            records.check_access_rule(access_mode)

        if require_employee:
            if not (self.env.is_admin() or self.env.user.has_group('base.group_user')):
                raise AccessError(_("Sorry, you are not allowed to access this document."))

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """
        Introduce search method based on user rights
        """
        ids = super(joint_event, self)._search(
            args, offset=offset, limit=limit, order=order, count=False, access_rights_uid=access_rights_uid,
        )

        if not ids:
            return count and 0 or []

        orig_ids = ids
        ids = set(ids)

        model_attachments = defaultdict(lambda: defaultdict(set))
        self._cr.execute(
            """SELECT id, res_model_domain, res_id, res_id_int FROM joint_event WHERE id IN %s""", [tuple(ids)]
        )
        for row in self._cr.dictfetchall():
            if not row['res_model_domain']:
                continue
            if row["res_model_domain"] == "mail.activity":
                activity = self.env[row["res_model_domain"]].browse(row["res_id_int"]).exists()
                if activity:
                    activity = activity.sudo()
                    model_attachments[activity.res_model][str(activity.res_id)].add(row['id'])
            else:
                model_attachments[row['res_model_domain']][row['res_id']].add(row['id'])

        for res_model, targets in model_attachments.items():
            if res_model not in self.env:
                continue
            if not self.env[res_model].check_access_rights('read', False):
                ids.difference_update(itertools.chain(*targets.values()))
                continue

            if res_model != "joint.event":
                # stand alone joint events are checked in _super
                target_ids_int = tuple(targets.keys())
                target_ids = [str(x) for x in target_ids_int]
                allowed_ids_int = [0] + self.env[res_model].with_context(active_test=False).search(
                    [('id', 'in', target_ids)]
                ).ids
                allowed_ids = [str(x) for x in allowed_ids_int]
                disallowed_ids = set(target_ids).difference(allowed_ids)

                for res_id in disallowed_ids:
                    for attach_id in targets[res_id]:
                        ids.remove(int(attach_id))

        result = [id for id in orig_ids if id in ids]

        if len(orig_ids) == limit and len(result) < len(orig_ids):
            result.extend(self._search(args, offset=offset + len(orig_ids),
                                       limit=limit, order=order, count=count,
                                       access_rights_uid=access_rights_uid)[:limit - len(result)])
        return len(result) if count else list(result)

    def read(self, fields_to_read=None, load='_classic_read'):
        self.check(mode='read')
        return super(joint_event, self).read(fields_to_read, load=load)

    def write(self, vals):
        self.check(mode='write', values=vals)
        return super(joint_event, self).write(vals)

    def copy(self, default=None):
        if default is None:
            default = {}
        self.check(mode='write')
        return super(joint_event, self).copy(default)

    def unlink(self):
        self.check(mode='unlink')
        res = super(joint_event, self).unlink()
        return res

    @api.model
    def create(self, vals):
        self.check(mode='write', values=vals)
        return super(joint_event, self).create(vals)