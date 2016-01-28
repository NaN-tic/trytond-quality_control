# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms. """
from collections import defaultdict
import datetime
from trytond.model import Workflow, ModelView, ModelSQL, fields, UnionMixin
from trytond.pyson import Bool, Equal, Eval, If, Not
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['Proof', 'ProofMethod', 'QualitativeValue', 'Template',
    'QualitativeTemplateLine', 'QuantitativeTemplateLine', 'TemplateLine',
    'QualityTest', 'QuantitativeTestLine', 'QualitativeTestLine']

__metaclass__ = PoolMeta

_PROOF_TYPES = [
    ('qualitative', 'Qualitative'),
    ('quantitative', 'Quantitative')
    ]
_TEST_STATE = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ]

_STATES = {
    'readonly': Eval('state') != 'draft',
    }


class Proof(ModelSQL, ModelView):
    'Quality Proof'
    __name__ = 'quality.proof'

    name = fields.Char('Name', required=True, translate=True,
        select=True)
    active = fields.Boolean('Active', select=True)
    company = fields.Many2One('company.company', 'Company', required=True,
        select=True)
    type = fields.Selection(_PROOF_TYPES, 'Type', required=True)
    methods = fields.One2Many('quality.proof.method', 'proof', 'Methods',
        required=True)

    @staticmethod
    def default_active():
        """ Return default value 'True' for active field """
        return True

    @staticmethod
    def default_company():
        """ Return default company value, context setted for company field """
        return Transaction().context.get('company')


class ProofMethod(ModelSQL, ModelView):
    'Quality Proof Method'
    __name__ = 'quality.proof.method'

    name = fields.Char('Name', required=True, translate=True,
        select=True)
    active = fields.Boolean('Active', select=True)
    proof = fields.Many2One('quality.proof', 'Proof', required=True)
    possible_values = fields.One2Many('quality.qualitative.value', 'method',
        'Possible Values',
        states={
            'invisible': ~Equal(Eval('_parent_proof', {}).get('type', ''),
                'qualitative'),
            'required': Equal(Eval('_parent_proof', {}).get('type', ''),
                'qualitative'),
            }, depends=['proof'])

    @staticmethod
    def default_active():
        return True


class QualitativeValue(ModelSQL, ModelView):
    'Quality Value'
    __name__ = 'quality.qualitative.value'

    name = fields.Char('Name', required=True, translate=True,
        select=True)
    active = fields.Boolean('Active', select=True)
    method = fields.Many2One('quality.proof.method', 'Method', required=True)

    @staticmethod
    def default_active():
        return True


class Template(ModelSQL, ModelView):
    'Quality Template'
    __name__ = 'quality.template'

    name = fields.Char('Name', required=True, translate=True,
        select=True)
    active = fields.Boolean('Active', select=True)
    company = fields.Many2One('company.company', 'Company', required=True,
        select=True)
    document = fields.Reference('Document', selection='get_model')
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    quantitative_lines = fields.One2Many('quality.quantitative.template.line',
        'template', 'Quantitative Lines')
    qualitative_lines = fields.One2Many('quality.qualitative.template.line',
        'template', 'Qualitative Lines')
    lines = fields.One2Many('quality.template.line', 'template', 'Lines')
    test = fields.One2Many('quality.test', 'template', 'Quality Test')

    @classmethod
    def get_model(cls):
        pool = Pool()
        ConfigLine = pool.get('quality.configuration.line')

        lines = ConfigLine.search([])
        res = [('', '')]
        for line in lines:
            res.append((line.document.model, line.document.name))
        return res

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class QualitativeTemplateLine(ModelSQL, ModelView):
    'Quality Qualitative Template Line'
    __name__ = 'quality.qualitative.template.line'

    template = fields.Many2One('quality.template', 'Template',
        ondelete='CASCADE', select=True, required=True)
    name = fields.Char('Name', required=True, translate=True, select=True)
    active = fields.Boolean('Active', select=True)
    proof = fields.Many2One('quality.proof', 'Proof', required=True, domain=[
            ('type', '=', 'qualitative'),
            ])
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof')),
            ], depends=['proof'])
    valid_value = fields.Many2One('quality.qualitative.value', 'Valid Value',
        required=True, domain=[
            ('method', '=', Eval('method')),
            ], depends=['method'])
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    sequence = fields.Integer('Sequence')

    @classmethod
    def __setup__(cls):
        super(QualitativeTemplateLine, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [table.sequence == None, table.sequence]

    @staticmethod
    def default_active():
        """ Return default value 'True' for active field """
        return True

    @fields.depends('proof')
    def on_change_proof(self):
        res = {}
        if not self.proof:
            res['method'] = None
            res['valid_value'] = None
        return res

    @fields.depends('method')
    def on_change_method(self):
        res = {}
        if not self.method:
            res['valid_value'] = None
        return res


class QuantitativeTemplateLine(ModelSQL, ModelView):
    'Quality Quantitative Template Line'
    __name__ = 'quality.quantitative.template.line'

    template = fields.Many2One('quality.template', 'Template',
        ondelete='CASCADE', select=True, required=True)
    name = fields.Char('Name', required=True, translate=True, select=True)
    active = fields.Boolean('Active', select=True)
    proof = fields.Many2One('quality.proof', 'Proof', required=True, domain=[
            ('type', '=', 'quantitative'),
            ])
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof')),
            ], depends=['proof'])
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    min_value = fields.Float('Min Value', digits=(16, Eval('unit_digits', 2)),
        required=True, depends=['unit_digits'])
    max_value = fields.Float('Max Value', digits=(16, Eval('unit_digits', 2)),
        required=True, depends=['unit_digits'])
    unit = fields.Many2One('product.uom', 'Unit', required=True)
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')
    sequence = fields.Integer('Sequence')

    @classmethod
    def __setup__(cls):
        super(QuantitativeTemplateLine, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [table.sequence == None, table.sequence]

    @staticmethod
    def default_active():
        return True

    @fields.depends('unit')
    def on_change_with_unit_digits(self, name=None):
        if not self.unit:
            return 2
        return self.unit.digits

    @fields.depends('proof')
    def on_change_proof(self):
        res = {}
        if not self.proof:
            res['method'] = None
        return res


class TemplateLine(UnionMixin, ModelSQL, ModelView):
    'Quality Template Line'
    __name__ = 'quality.template.line'

    template = fields.Many2One('quality.template', 'Template', required=True)
    name = fields.Char('Name', required=True, translate=True, select=True)
    proof = fields.Many2One('quality.proof', 'Proof', required=True)
    active = fields.Boolean('Active', select=True)
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof')),
            ],
        depends=['proof'])
    type = fields.Selection('get_types', 'Type', required=True, readonly=True)
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    sequence = fields.Integer('Sequence')

    @classmethod
    def __setup__(cls):
        super(TemplateLine, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [table.sequence == None, table.sequence]

    @staticmethod
    def union_models():
        return ['quality.qualitative.template.line',
            'quality.quantitative.template.line']

    @classmethod
    def get_types(cls):
        Model = Pool().get('ir.model')
        models = cls.union_models()
        models = Model.search([
                ('model', 'in', models),
                ])
        return [(m.model, m.name) for m in models]

    @classmethod
    def union_column(cls, name, field, table, Model):
        if name == 'type':
            return Model.__name__
        return super(TemplateLine, cls).union_column(name, field, table, Model)

    @classmethod
    def write(cls, *args):
        pool = Pool()
        models_to_write = defaultdict(list)
        # Check Permisions
        super(TemplateLine, cls).write(*args)
        actions = iter(args)
        for models, values in zip(actions, actions):
            for model in models:
                record = cls.union_unshard(model.id)
                models_to_write[record.__name__].extend(([record], values))
        for model, arguments in models_to_write.iteritems():
            Model = pool.get(model)
            Model.write(*arguments)


class QualityTest(Workflow, ModelSQL, ModelView):
    'Quality Test'
    __name__ = 'quality.test'
    _rec_name = 'number'

    number = fields.Char('Number', readonly=True, select=True,
        states={'required': Not(Equal(Eval('state'), 'draft'))})
    active = fields.Boolean('Active', select=True)
    company = fields.Many2One('company.company', 'Company', required=True,
        select=True, states=_STATES, depends=['state'])
    document = fields.Reference('Document', selection='get_model',
        required=True, states=_STATES, depends=['state'])
    test_date = fields.DateTime('Date', states=_STATES, depends=['state'])
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    quantitative_lines = fields.One2Many('quality.quantitative.test.line',
        'test', 'Quantitative Lines', states=_STATES, depends=['state'])
    qualitative_lines = fields.One2Many('quality.qualitative.test.line',
        'test', 'Qualitative Lines', states=_STATES, depends=['state'])
    template = fields.Many2One('quality.template', 'Template', states=_STATES,
        depends=['state'])
    success = fields.Function(fields.Boolean('Success'), 'get_success')
    confirmed_date = fields.DateTime('Confirmed Date', readonly=True,
        states={
            'invisible': Eval('state') == 'draft',
            },
        depends=['state'])
    state = fields.Selection(_TEST_STATE, 'State',
        readonly=True, required=True)

    @classmethod
    def get_model(cls):
        pool = Pool()
        ConfigLines = pool.get('quality.configuration.line')

        lines = ConfigLines.search([])
        res = [('', '')]
        for line in lines:
            res.append((line.document.model, line.document.name))
        return res

    def get_success(self, name):
        for line in self.quantitative_lines:
            if not line.success:
                return False
        for line in self.qualitative_lines:
            if not line.success:
                return False
        return True

    @classmethod
    def __setup__(cls):
        super(QualityTest, cls).__setup__()
        cls._transitions |= set((
            ('draft', 'confirmed'),
            ('confirmed', 'draft'),
            ('confirmed', 'successful'),
            ('confirmed', 'failed'),
            ('successful', 'draft'),
            ('failed', 'draft'),
            ))

        cls._buttons.update({
            'confirmed': {
                'invisible': (Eval('state') != 'draft'),
                'icon': 'tryton-go-next',
                },
            'manager_validate': {
                'invisible': (Eval('state') != 'confirmed'),
                'icon': 'tryton-ok',
                },
            'draft': {
                'invisible': (Eval('state') == 'draft'),
                },
            'set_template': {
                'readonly': ((Eval('state') != 'draft')
                        | ~Bool(Eval('template'))),
                },
            })

    @staticmethod
    def default_test_date():
        return datetime.datetime.now()

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_template():
        return Transaction().context.get('default_quality_template')

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, tests):
        cls.write(tests, {'confirmed_date': None})

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirmed(cls, tests):
        cls.set_number(tests)
        cls.write(tests, {'confirmed_date': datetime.datetime.now()})

    @classmethod
    @Workflow.transition('successful')
    def successful(cls, tests):
        pass

    @classmethod
    @Workflow.transition('failed')
    def failed(cls, tests):
        pass

    @classmethod
    @ModelView.button
    def manager_validate(cls, tests):
        for test in tests:
            if test.success:
                cls.successful(tests)
            else:
                cls.failed(tests)

    @classmethod
    def set_number(cls, tests):
        pool = Pool()
        ConfigLine = pool.get('quality.configuration.line')
        Model = pool.get('ir.model')
        Sequence = pool.get('ir.sequence')

        for test in tests:
            doc = str(test.document).split(',')[0]
            model, = Model.search([('model', '=', doc)])
            config, = ConfigLine.search([('document', '=', model.id)])
            sequence = config.quality_sequence
            test.number = Sequence.get_id(sequence.id)
            test.save()

    def set_template_vals(self):
        pool = Pool()
        QualitativeLine = pool.get('quality.qualitative.test.line')
        QuantitativeLine = pool.get('quality.quantitative.test.line')
        ql_lines = []
        for ql in self.template.qualitative_lines:
            line = QualitativeLine()
            line.set_template_line_vals(ql)
            ql_lines.append(line)
        self.qualitative_lines = ql_lines

        qt_lines = []
        for qt in self.template.quantitative_lines:
            line = QuantitativeLine()
            line.set_template_line_vals(qt)
            qt_lines.append(line)
        self.quantitative_lines = qt_lines

    @classmethod
    @ModelView.button
    def set_template(cls, tests):
        for test in tests:
            test.set_template_vals()
            test.save()


class QualitativeTestLine(ModelSQL, ModelView):
    'Quality Qualitative Line'
    __name__ = 'quality.qualitative.test.line'

    test = fields.Many2One('quality.test', 'Test',
        ondelete='CASCADE', select=True)
    test_state = fields.Function(fields.Selection(_TEST_STATE, 'Test State'),
        'get_test_state')
    template_line = fields.Many2One('quality.qualitative.template.line',
        'Template Line')
    name = fields.Char('Name', required=True, translate=True, select=True)
    proof = fields.Many2One('quality.proof', 'Proof', required=True, domain=[
            ('type', '=', 'qualitative'),
            ],
        states={
            'readonly': Bool(Eval('template_line')),
            }, depends=['template_line'])
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof')),
            ],
        states={
            'readonly': Bool(Eval('template_line')),
            }, depends=['proof', 'template_line'])
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    test_value = fields.Many2One('quality.qualitative.value', 'Test Value',
        required=True, domain=[
            ('method', '=', Eval('method')),
            ],
        states={
            'readonly': Bool(Eval('template_line')),
            }, depends=['method', 'template_line'])
    value = fields.Many2One('quality.qualitative.value', 'Value', domain=[
            ('method', '=', Eval('method')),
            ], depends=['method'])
    success = fields.Function(fields.Boolean('Success'), 'get_success')
    sequence = fields.Integer('Sequence')

    @classmethod
    def __setup__(cls):
        super(QualitativeTestLine, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [table.sequence == None, table.sequence]

    def get_success(self, name=None):
        if self.value == self.test_value:
            return True
        return False

    def test_state(self):
        return self.test.state

    def set_template_line_vals(self, template_line):
        self.name = template_line.name
        self.proof = template_line.proof
        self.method = template_line.method
        self.internal_description = template_line.internal_description
        self.external_description = template_line.external_description
        self.test_value = template_line.valid_value
        self.sequence = template_line.sequence


class QuantitativeTestLine(ModelSQL, ModelView):
    'Quality Quantitative Line'
    __name__ = 'quality.quantitative.test.line'

    test = fields.Many2One('quality.test', 'Test',
        ondelete='CASCADE', select=True, required=True)
    test_state = fields.Function(fields.Selection(_TEST_STATE, 'Test State'),
        'get_test_state')
    template_line = fields.Many2One('quality.quantitative.template.line',
        'Template Line', readonly=True)
    name = fields.Char('Name', required=True, translate=True, select=True,
        states={
            'readonly': Bool(Eval('template_line', 0)),
            }, depends=['template_line'])
    proof = fields.Many2One('quality.proof', 'Proof', required=True, domain=[
            ('type', '=', 'quantitative'),
            ],
        states={
            'readonly': Bool(Eval('template_line', 0)),
            }, depends=['template_line'])
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof')),
            ],
        states={
            'readonly': Bool(Eval('template_line', 0)),
            }, depends=['proof', 'template_line'])
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    unit_range = fields.Many2One('product.uom', 'Unit Range', required=True,
        states={
            'readonly': Bool(Eval('template_line', 0)),
            }, depends=['template_line'])
    unit_range_digits = fields.Function(fields.Integer('Unit Range Digits'),
        'on_change_with_unit_range_digits')
    unit_range_category = fields.Function(
        fields.Many2One('product.uom.category', 'Unit Range Category'),
        'on_change_with_unit_range_category')
    min_value = fields.Float('Min Value',
        digits=(16, Eval('unit_range_digits', 2)), required=True,
        states={
            'readonly': Bool(Eval('template_line', 0)),
            },
        depends=['unit_range_digits', 'template_line'])
    max_value = fields.Float('Max Value',
        digits=(16, Eval('unit_range_digits', 2)), required=True,
        states={
                'readonly': Bool(Eval('template_line', 0)),
            },
        depends=['unit_range_digits', 'template_line'])
    value = fields.Float('Value', digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits', 'test_state'])
    unit = fields.Many2One('product.uom', 'Unit',
        domain=[
            If(Bool(Eval('unit_range_category')),
                ('category', '=', Eval('unit_range_category')),
                ('category', '!=', -1)),
            ],
        states={
            'required': Bool(Eval('value')),
        },
        depends=['unit_range_category', 'value'])
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')
    success = fields.Function(fields.Boolean('Success'), 'get_success')
    sequence = fields.Integer('Sequence')

    @classmethod
    def __setup__(cls):
        super(QuantitativeTestLine, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [table.sequence == None, table.sequence]

    @classmethod
    def get_test_state(self, lines, name):
        res = {}
        for line in lines:
            res[line.id] = line.test.state
        return res

    @fields.depends('unit_range')
    def on_change_with_unit_range_digits(self, name=None):
        if not self.unit_range:
            return 2
        return self.unit_range.digits

    @fields.depends('unit_range')
    def on_change_with_unit_range_category(self, name=None):
        if self.unit_range:
            return self.unit_range.category.id

    @fields.depends('unit')
    def on_change_with_unit_digits(self, name=None):
        if not self.unit:
            return 2
        return self.unit.digits

    @classmethod
    def get_success(self, lines, name):
        res = {}
        pool = Pool()
        Uom = pool.get('product.uom')
        for line in lines:
            res[line.id] = False
            value = line.value
            value = Uom.compute_qty(line.unit, value, line.unit_range)
            if value >= line.min_value and value <= line.max_value:
                res[line.id] = True
        return res

    def set_template_line_vals(self, template_line):
        self.template_line = template_line
        self.name = template_line.name
        self.proof = template_line.proof
        self.method = template_line.method
        self.internal_description = template_line.internal_description
        self.external_description = template_line.external_description
        self.min_value = template_line.min_value
        self.max_value = template_line.max_value
        self.unit_range = template_line.unit
        self.unit = template_line.unit
        self.sequence = template_line.sequence
