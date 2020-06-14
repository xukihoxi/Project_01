# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
import time
from datetime import date
from odoo.exceptions import UserError, ValidationError
import logging
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


ones = ["", "một ", "hai ", "ba ", "bốn ", "năm ", "sáu ", "bảy ", "tám ", "chín ", "mười ", "mười một ", "mười hai ",
        "mười ba ", "mười bốn ", "mười lăm ", "mười sáu ", "mười bảy ", "mười tám ", "mười chín "]
twenties = ["", "", "hai mươi ", "ba mươi ", "bốn mươi ", "năm mươi ", "sáu mươi ", "bảy mươi ", "tám mươi ", "chín mươi "]
thousands = ["", "nghìn ", "triệu ", "tỉ ", "nghìn ", "triệu ", "tỉ "]


def num999(n, next):
    c = n % 10  # singles digit
    b = int(((n % 100) - c) / 10)  # tens digit
    a = int(((n % 1000) - (b * 10) - c) / 100)  # hundreds digit
    t = ""
    h = ""
    if a != 0 and b == 0 and c == 0:
        t = ones[a] + "trăm "
    elif a != 0:
        t = ones[a] + "trăm "
    elif a == 0 and b == 0 and c == 0:
        t = ""
    elif a == 0 and next != '':
        t = "không trăm "
    if b == 1:
        h = ones[n % 100]
    if b == 0:
        if a > 0 and c > 0:
            h = "linh " + ones[n % 100]
        else:
            h = ones[n % 100]
    elif b > 1:
        if c == 4:
            tmp = "tư "
        elif c == 1:
            tmp = "mốt "
        else:
            tmp = ones[c]
        h = twenties[b] + tmp
    st = t + h
    return st


def num2word(num):
    if not isinstance(num, int):
        raise ValidationError("Number to convert to words must be integer")
    if num == 0: return 'không'
    i = 3
    n = str(num)
    word = ""
    k = 0
    while (i == 3):
        nw = n[-i:]
        n = n[:-i]
        int_nw = int(float(nw))
        if int_nw == 0:
            word = num999(int_nw, n) + thousands[int_nw] + word
        else:
            word = num999(int_nw, n) + thousands[k] + word
        if n == '':
            i += 1
        k += 1
    return word[:-1].capitalize()


class AccountCash(models.Model):
    _name = 'account.cash'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.multi
    @api.one
    def _amount_total(self):
        amount = 0
        for line in self.lines:
            amount += line.value
        self.amount_total = amount

    @api.multi
    def _default_branch_id(self):
        branch_id = self.env['res.users'].browse(self._uid).branch_id.id
        return branch_id

    def _default_session(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        return self.env['pos.session'].search([('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)

    @api.multi
    def _default_jounal(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        session_id =  self.env['pos.session'].search([('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)
        for line in session_id.statement_ids:
            if session_id.config_id.x_journal_currency_ids:
                if line.journal_id.type == 'cash' and line.journal_id.id not in (session_id.config_id.x_journal_currency_ids.ids):
                    return line.journal_id
            else:
                if line.journal_id.type == 'cash':
                    return line.journal_id

    name = fields.Char('Number', default='/', readonly=True)
    type = fields.Selection(selection=[('out', 'Cash out'), ('in', 'Cash in')], default='out', required=True, string='Type')
    partner_id = fields.Many2one('res.partner', 'Payer/Receiver')
    reason = fields.Text('Reason', required=True)
    journal_id = fields.Many2one('account.journal', 'Payment method', default=_default_jounal)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 states={'draft': [('readonly', False)], 'refused': [('readonly', False)]},
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  states={'draft': [('readonly', False)], 'refused': [('readonly', False)]},
                                  default=lambda self: self.env.user.company_id.currency_id)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          states={'post': [('readonly', True)], 'done': [('readonly', True)]},
                                          oldname='analytic_account')
    date = fields.Date('Date', default=fields.Date.context_today)
    ref = fields.Char('Reference')
    lines = fields.One2many('account.cash.line', 'cash_id')
    note = fields.Text('Note')
    amount_total = fields.Float('Total bill', compute='_amount_total')
    move_id = fields.Many2one('account.move', string='Account entry')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('approval', 'Approval'),
        ('done', 'Done'),
        ('refuse', 'Refused'),
    ], 'State', default='draft', track_visibility='onchange')

    create_uid = fields.Many2one('res.users', 'Creator', default=lambda s: s._uid)
    director = fields.Many2one('res.users', 'Director')
    cashier = fields.Many2one('res.users', 'Cashier')
    branch_id = fields.Many2one('res.branch', default=_default_branch_id)
    session_id = fields.Many2one('pos.session', "Session", default=_default_session)

    _sql_constraints = [
        ('name_unique', 'unique(name)', "Ticket's name must be unique!")
    ]

    @api.onchange('session_id')
    def _onchange_session_id(self):
        ids = []
        session_obj = self.env['pos.session'].search([('branch_id', '=', self.branch_id.id), ('state', '=', 'opened')])
        for line in session_obj:
                ids.append(line.id)
        journal_ids = []
        if self.session_id:
            for line in self.session_id.config_id.journal_ids:
                if line.type in ('bank', 'cash'):
                    journal_ids.append(line.id)
        return {
            'domain': {
                'session_id': [('id', 'in', ids)],
                'journal_id': [('id', 'in', journal_ids)]
            }
        }


    @api.multi
    def action_reset(self):
        for r in self:
            if r.state == 'refuse':
                r.state = 'draft'

    @api.model
    def refuse(self, reason):
        self.state = 'refuse'
        self.message_post(body=_("Request is refused with reason: ") + reason, subtype="mail.mt_note")

    @api.model
    def create(self, vals):
        seq_obj = self.env['ir.sequence']
        if vals.get('type') == 'in':
            number = seq_obj.next_by_code('cash_in_seq')
        else:
            number = seq_obj.next_by_code('cash_out_seq')
        vals['name'] = number
        return super(AccountCash, self).create(vals)

    def list_period(self):
        query = "SELECT id,code from account_period order by code"
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        period = []
        for r in res:
            code = r['code'] and r['code'] or ''
            period.append((r['id'], code))
        return period

    @api.multi
    def action_confirm(self):
        self.write({'state': 'confirm'})
        return True

    # @api.multi
    # def action_approval(self):
    #     self.write({'state': 'approval'})
    #     self.action_carrying()
    #     return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_carrying(self):
        if self.state == 'done':
            raise UserError("Record has been posted! Refresh your browser, please")

        move_lines = []
        _in = (self.type == 'in')

        amount = 0
        for line in self.lines:
            # Ghi sổ trả/nhận của các đối tác
            amount += line.value
            debit_move_vals = {
                'name': self.name,
                'ref': self.reason,
                'date': self.date,
                'account_id': line.account_id.id,
                'debit': 0.0 if _in else line.value,
                'credit': line.value if _in else 0.0,
                'partner_id': line.partner_id.id if line.partner_id else self.partner_id.id,
                'product_id': line.product_id.id,
            }
            move_lines.append((0, 0, debit_move_vals))
        if amount <= 0:
            raise UserError("Total amount must be greater than 0")

        # Ghi sổ thu/chi của công ty
        credit_move_vals = {
            'ref': self.reason,
            'name': self.name,
            'date': self.date,
            'account_id': _in and self.journal_id.default_debit_account_id.id or self.journal_id.default_credit_account_id.id,
            'debit': amount if _in else 0.0,
            'credit': 0 if _in else amount,
            'partner_id': self.company_id.partner_id.id,
        }
        move_lines.append((0, 0, credit_move_vals))

        move_vals = {
            'ref': self.reason,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'line_ids': move_lines,
        }
        move_id = self.env['account.move'].create(move_vals)
        self.write({'move_id': move_id.id})
        self.move_id.post()

        self.write({'state': 'done'})
        # Tạo account_bank_statemant_line nếu khi sử dụng phiếu thu chi có liên quan đến phiên
        if self.session_id:
            statement_id = False
            for statement in self.session_id.statement_ids:
                if statement.id == statement_id:
                    journal_id = statement.journal_id.id
                    break
                elif statement.journal_id.id == self.journal_id.id:
                    statement_id = statement.id
                    break
            company_cxt = dict(self.env.context, force_company=self.journal_id.company_id.id)
            account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
                                                                                'res.partner')
            account_id = (self.partner_id.property_account_receivable_id.id) or (
                    account_def and account_def.id) or False
            for line in self.lines:
                amount = line.value
                if self.type == 'out':
                    amount = - line.value
                argvs = {
                    'ref': self.name,
                    'name': 'Thu_Chi',
                    'partner_id': line.partner_id.id,
                    'amount': amount,
                    'account_id': account_id,
                    'statement_id': statement_id,
                    'journal_id': self.journal_id.id,
                    'date': self.date,
                    'x_ignore_reconcile': True,
                    'note': self.reason,
                }
                pos_make_payment_id = self.env['account.bank.statement.line'].create(argvs)
                line.partner_id.x_loyal_total = line.partner_id.x_loyal_total + amount
                revenue = self.env['crm.vip.customer.revenue'].create({
                    'partner_id': line.partner_id.id,
                    'journal_id': self.journal_id.id,
                    'amount': amount,
                    'date': self.date,
                    'order_id': False,
                })
        return True

    @api.multi
    def unlink(self):
        for r in self:
            if r.state != 'draft':
                raise UserError('You can only delete record in Draft state!')
        return super(AccountCash, self).unlink()

    @api.model
    def get_amount_word(self):
        res = num2word(int(self.amount_total))
        if self.currency_id.currency_unit_label:
            res += ' ' + self.currency_id.currency_unit_label.lower()
        return res

    @api.model
    def get_debit_credit_list(self):
        res = {'debit': {}, 'credit': {}}
        if self.move_id:
            for line in self.move_id.line_ids:
                if line.debit > 0:
                    res['debit'][line.account_id.code] = line.debit
                if line.credit > 0:
                    res['credit'][line.account_id.code] = line.credit
        return res


class AccountCashLine(models.Model):
    _name = 'account.cash.line'
    #
    # @api.model
    # def default_get(self, fields_list):
    #     res = super(AccountCashLine, self).default_get(fields_list)
    #
    #     if 'cash_partner_id' in self._context:
    #         res['partner_id'] = self._context['cash_partner_id']
    #     return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        # cash_type = self._context.get('cash_type', False)
        if self.product_id and not self.account_id:
            if self.cash_id.type == 'in':
                self.account_id = self.product_id.property_account_income_id
            else:
                self.account_id = self.product_id.property_account_expense_id

    cash_id = fields.Many2one('account.cash')
    name = fields.Char('Description')
    value = fields.Float('Value', required=True)
    product_id = fields.Many2one('product.product', string='Category',
                                 states={'draft': [('readonly', False)],
                                         'reported': [('readonly', False)],
                                         'refused': [('readonly', False)]},
                                 domain=[('can_be_expensed', '=', True)])
    account_id = fields.Many2one('account.account', 'Account')
    partner_id = fields.Many2one('res.partner', 'Partner')
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments", ondelete='cascade')

