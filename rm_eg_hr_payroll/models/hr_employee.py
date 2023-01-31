# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################


from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    religion = fields.Selection(
        [('mus', 'Muslem'), ('chris', 'Christian'), ('other', 'Others')],
        string="Religion")
    military_status = fields.Selection(
        [('not_req', 'Not Required'), ('post', 'Postponed'),
         ('complete', 'complete'), ('exemption', 'Exemption'),
         ('current', 'Currently serving ')], string="Military Status")
    age = fields.Integer(string="Age", compute="_calculate_age", readonly=True)
    start_date = fields.Date(string="Start Working At")
    edu_major = fields.Char(string="major")
    edu_grad = fields.Selection(
        [('ex', 'Excellent'), ('vgod', 'Very Good'), ('god', 'Good'),
         ('pas', 'Pass')],
        string="Grad")
    edu_note = fields.Text("Education Notes")
    experience_y = fields.Integer(compute="_calculate_experience",
                                  string="Experience",
                                  help="experience in our company", store=True)
    experience_m = fields.Integer(compute="_calculate_experience",
                                  string="Experience monthes", store=True)
    experience_d = fields.Integer(compute="_calculate_experience",
                                  string="Experience dayes", store=True)
    absence_counter = fields.Integer()

    @api.depends("birthday")
    def _calculate_age(self):
        for emp in self:
            if emp.birthday:
                dob = emp.birthday
                emp.age = int((datetime.today().date() - dob).days / 365)
            else:
                emp.age = 0

    @api.depends("start_date")
    def _calculate_experience(self):
        for emp in self.search([]):
            if emp.start_date:
                date_format = '%Y-%m-%d'
                current_date = (datetime.today()).strftime(date_format)
                d1 = emp.start_date
                d2 = datetime.strptime(current_date, date_format).date()
                r = relativedelta(d2, d1)
                emp.experience_y = r.years
                emp.experience_m = r.months
                emp.experience_d = r.days
            else:
                emp.experience_y = 0
                emp.experience_m = 0
                emp.experience_d = 0

    @api.model
    def _cron_employee_age(self):
        self._calculate_age()

    @api.model
    def _cron_employee_exp(self):
        self._calculate_experience()

    def calculate_time_off(self, wage_hour, date_from, date_to):
        # search for all timeoff by  hour
        timeoff_type_objs = self.env.ref('rm_eg_hr_payroll.holiday_status_timeoffhour').id
        timeoff_objs = self.env['hr.leave'].search([('holiday_status_id', '=', timeoff_type_objs), ('state', '=', 'validate'),
                                                    ('date_from', '>=', date_from), ('date_to', '<=', date_to),
                                                    ('employee_id', '=', self.id)])
        total_hours = 0.0
        if timeoff_objs:
            total_hours = sum(float(timeoff_obj.number_of_hours_display) for timeoff_obj in timeoff_objs)
            return (total_hours * wage_hour) * -1
        return 0

    def calculate_time_off_ded(self, wage_hour, date_from, date_to):
        # search for all timeoff by  hour
        timeoff_type_objs = self.env.ref('rm_eg_hr_payroll.holiday_status_timeoffhour_ded').id
        timeoff_objs = self.env['hr.leave'].search([('holiday_status_id', '=', timeoff_type_objs), ('state', '=', 'validate'),
                                                    ('date_from', '>=', date_from), ('date_to', '<=', date_to),
                                                    ('employee_id', '=', self.id)])
        total_hours = 0.0
        if timeoff_objs:
            total_hours = sum(float(timeoff_obj.number_of_hours_display) for timeoff_obj in timeoff_objs)
            return (total_hours * wage_hour) * -1
        return 0

    def calculate_allowance_rule_request_actualdiffabsent(self, wage_hour, date_from, date_to):
        # search for all timeoff by  hour
        timeoff_type_objs = self.env.ref('rm_eg_hr_payroll.holiday_status_timeoffhour').id
        timeoff_objs = self.env['hr.leave'].search([('holiday_status_id', '=', timeoff_type_objs), ('state', '=', 'validate'),
                                                    ('date_from', '>=', date_from), ('date_to', '<=', date_to), ('employee_id', '=', self.id)])
        total_hours = 0.0
        if timeoff_objs:
            # search for attendance in this day if no attendance i will call late diff then return it as deduction
            for timeoff_obj in timeoff_objs:
                hr_attendance_objs = self.env['hr.attendance'].search(
                    [('check_in', '>=', timeoff_obj.request_date_from), ('check_out', '<=', timeoff_obj.request_date_from),
                     ('employee_id', '=', self.id)])
                if not hr_attendance_objs:
                    # search in attendance sheet to get validated attendance sheet for this employee in this period
                    hr_attendance_sheet_objs = self.env['attendance.sheet'].search([('employee_id', '=', self.id), ('state', '=', 'done'),
                                                                                    ('date_from', '>=', timeoff_obj.request_date_from),
                                                                                    ('date_to', '<=', timeoff_obj.request_date_from)])
                    # seach in attendance sheet line to get the actual diff time
                    for hr_attendance_sheet_obj in hr_attendance_sheet_objs:
                        hr_attendance_sheet_line_objs = self.env['attendance.sheet.line'].search(
                            [('date', '>=', hr_attendance_sheet_obj.date_from), ('date', '<=', hr_attendance_sheet_obj.date_to),
                             ('att_sheet_id', '=', hr_attendance_sheet_obj.id)])
                        total_hours = sum(
                            float(hr_attendance_sheet_line_obj.act_diff_time) for hr_attendance_sheet_line_obj in hr_attendance_sheet_line_objs)
        return (total_hours * wage_hour) * -1
