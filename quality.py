# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from collections import defaultdict
import datetime
from sql import Column, Literal
from trytond.model import Workflow, ModelView, ModelSQL, DeactivableMixin, fields
from trytond.model import Unique, UnionMixin, sequence_ordered
from trytond.pyson import Bool, Equal, Eval, If, Not
from trytond.transaction import Transaction
from trytond.pool import Pool

__all__ = ['Proof', 'ProofMethod',
    'QualitativeValue', 'Template',
    'QualitativeTemplateLine', 'QuantitativeTemplateLine', 'TemplateLine',
    'QualityTest', 'QuantitativeTestLine', 'QualitativeTestLine', 'TestLine',
    'QualityTestQualityTemplate']

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
_DEPENDS = ['state']


class Proof(DeactivableMixin, ModelSQL, ModelView):
    'Quality Proof'
    __name__ = 'quality.proof'
    name = fields.Char('Name', required=True, translate=True)
    type = fields.Selection(_PROOF_TYPES, 'Type', required=True)
    methods = fields.One2Many('quality.proof.method', 'proof', 'Methods')

    @classmethod
    def __register__(cls, module_name):
        table = cls.__table_handler__(module_name)

        super(Proof, cls).__register__(module_name)
        # Migration from 5.4: Drop company
        if table.column_exist('company'):
            table.drop_column('company')


class ProofMethod(DeactivableMixin, ModelSQL, ModelView):
    'Quality Proof Method'
    __name__ = 'quality.proof.method'

    name = fields.Char('Name', required=True, translate=True)
    proof = fields.Many2One('quality.proof', 'Proof', required=True)
    possible_values = fields.One2Many('quality.qualitative.value', 'method',
        'Possible Values',
        states={
            'invisible': ~Equal(Eval('_parent_proof', {}).get('type', ''),
                'qualitative'),
            'required': Equal(Eval('_parent_proof', {}).get('type', ''),
                'qualitative'),
            })


class QualitativeValue(DeactivableMixin, ModelSQL, ModelView):
    'Quality Value'
    __name__ = 'quality.qualitative.value'

    name = fields.Char('Name', required=True, translate=True)
    method = fields.Many2One('quality.proof.method', 'Method', required=True)


class Template(DeactivableMixin, ModelSQL, ModelView):
    'Quality Template'
    __name__ = 'quality.template'

    name = fields.Char('Name', required=True, translate=True)
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    quantitative_lines = fields.One2Many('quality.quantitative.template.line',
        'template', 'Quantitative Lines')
    qualitative_lines = fields.One2Many('quality.qualitative.template.line',
        'template', 'Qualitative Lines')
    lines = fields.One2Many('quality.template.line', 'template', 'Lines')

    @classmethod
    def __register__(cls, module_name):
        table = cls.__table_handler__(module_name)
        super().__register__(module_name)
        # Migration from 6.4: Drop company
        if table.column_exist('company'):
            table.drop_column('company')

    @classmethod
    def copy(cls, templates, default=None):
        if default is None:
            default = {}
        if 'lines' not in default:
            default['lines'] = None
        return super(Template, cls).copy(templates, default)


class QualitativeTemplateLine(sequence_ordered(), DeactivableMixin, ModelSQL, ModelView):
    'Quality Qualitative Template Line'
    __name__ = 'quality.qualitative.template.line'

    template = fields.Many2One('quality.template', 'Template',
        ondelete='CASCADE', required=True)
    name = fields.Char('Name', required=True, translate=True)
    proof = fields.Many2One('quality.proof', 'Proof', required=True, domain=[
            ('type', '=', 'qualitative'),
            ])
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof', -1)),
            ])
    valid_value = fields.Many2One('quality.qualitative.value', 'Valid Value',
        required=True, domain=[
            ('method', '=', Eval('method', -1)),
            ])
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')

    @fields.depends('proof')
    def on_change_proof(self):
        if not self.proof:
            self.method = None
            self.valid_value = None

    @fields.depends('method')
    def on_change_method(self):
        if not self.method:
            self.valid_value = None


class QuantitativeTemplateLine(sequence_ordered(), DeactivableMixin, ModelSQL, ModelView):
    'Quality Quantitative Template Line'
    __name__ = 'quality.quantitative.template.line'

    template = fields.Many2One('quality.template', 'Template',
        ondelete='CASCADE', required=True)
    name = fields.Char('Name', required=True, translate=True)
    proof = fields.Many2One('quality.proof', 'Proof', required=True, domain=[
            ('type', '=', 'quantitative'),
            ])
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof', -1)),
            ])
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    min_value = fields.Float('Min Value', digits='unit',
        required=True)
    max_value = fields.Float('Max Value', digits='unit',
        required=True)
    unit = fields.Many2One('product.uom', 'Unit', required=True)

    @fields.depends('proof')
    def on_change_proof(self):
        if not self.proof:
            self.method = None


class TemplateLine(UnionMixin, ModelSQL, ModelView, DeactivableMixin, sequence_ordered()):
    'Quality Template Line'
    __name__ = 'quality.template.line'

    template = fields.Many2One('quality.template', 'Template', required=True)
    name = fields.Char('Name', required=True, translate=True)
    proof = fields.Many2One('quality.proof', 'Proof', required=True)
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof', -1)),
            ])
    type = fields.Selection('get_types', 'Type', required=True, readonly=True)
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    valid_value = fields.Many2One('quality.qualitative.value', 'Valid Value',
        required=True, domain=[
            ('method', '=', Eval('method', -1)),
            ])
    min_value = fields.Float('Min Value', digits='unit')
    max_value = fields.Float('Max Value', digits='unit')
    unit = fields.Many2One('product.uom', 'Unit')

    @classmethod
    def union_models(cls):
        return ['quality.qualitative.template.line',
            'quality.quantitative.template.line']

    @classmethod
    def get_types(cls):
        Model = Pool().get('ir.model')
        models = cls.union_models()
        models = Model.search([
                ('name', 'in', models),
                ])
        return [(m.name, m.string) for m in models]

    @classmethod
    def union_column(cls, name, field, table, Model):
        if name == 'type':
            return Model.__name__
        return super(TemplateLine, cls).union_column(name, field, table, Model)

    @classmethod
    def write(cls, *args):
        pool = Pool()
        models_to_write = defaultdict(list)
        # Do not call super() as it would raise NotImplemented
        actions = iter(args)
        for models, values in zip(actions, actions):
            for model in models:
                record = cls.union_unshard(model.id)
                models_to_write[record.__name__].extend(([record], values))
        for model, arguments in models_to_write.items():
            Model = pool.get(model)
            Model.write(*arguments)

    @classmethod
    def delete(cls, lines):
        pool = Pool()
        models_to_delete = defaultdict(list)
        # Do not call super() as it would raise NotImplemented
        for model in lines:
            record = cls.union_unshard(model.id)
            models_to_delete[record.__name__].append(record)
        for model, records in models_to_delete.items():
            Model = pool.get(model)
            Model.delete(records)


class QualityTest(DeactivableMixin, Workflow, ModelSQL, ModelView):
    'Quality Test'
    __name__ = 'quality.test'
    _rec_name = 'number'

    number = fields.Char('Number', readonly=True,
        states={'required': Not(Equal(Eval('state'), 'draft'))})
    company = fields.Many2One('company.company', 'Company', required=True,
        states=_STATES)
    document = fields.Reference('Document', selection='get_model',
        required=True, states=_STATES)
    test_date = fields.DateTime('Date', states=_STATES)
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    quantitative_lines = fields.One2Many('quality.quantitative.test.line',
        'test', 'Quantitative Lines', states=_STATES)
    qualitative_lines = fields.One2Many('quality.qualitative.test.line',
        'test', 'Qualitative Lines', states=_STATES)
    lines = fields.One2Many('quality.test.line', 'test', 'Lines')
    templates = fields.Many2Many('quality.test-quality.template',
        'test', 'template', 'Tests', states=_STATES)
    success = fields.Function(fields.Boolean('Success'), 'get_success')
    confirmed_date = fields.DateTime('Confirmed Date', readonly=True,
        states={
            'invisible': Eval('state') == 'draft',
            })
    state = fields.Selection(_TEST_STATE, 'State',
        readonly=True, required=True)

    @classmethod
    def get_model(cls):
        pool = Pool()
        ConfigLines = pool.get('quality.configuration.line')

        lines = ConfigLines.search([])
        res = [('', '')]
        for line in lines:
            res.append((line.document.name, line.document.string))
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
                'icon': 'tryton-forward',
                },
            'manager_validate': {
                'invisible': (Eval('state') != 'confirmed'),
                'icon': 'tryton-ok',
                },
            'draft': {
                'invisible': (Eval('state') == 'draft'),
                'icon': 'tryton-clear',
                },
            'apply_templates': {
                'readonly': (
                        (Eval('state') != 'draft') |
                        ~Bool(Eval('templates')) |
                        Bool(Eval('quantitative_lines')) |
                        Bool(Eval('qualitative_lines')))
                },
            })

    @staticmethod
    def default_test_date():
        return datetime.datetime.now()

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    def get_rec_name(self, name):
        res = self.number or ''
        if self.document:
            res += ' @ ' + self.document.rec_name
        return res

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
        for test in tests:
            if test.number:
                continue
            doc = str(test.document).split(',')[0]
            model, = Model.search([('name', '=', doc)])
            config = ConfigLine.search([('document', '=', model.id)])[0]
            test.number = config.quality_sequence.get()
            test.save()

    @staticmethod
    def set_qualitative_vals(test):
        # test -> quality.template
        QualitativeLine = Pool().get('quality.qualitative.test.line')

        ql_lines = []
        for ql in test.qualitative_lines:
            line = QualitativeLine()
            line.set_template_line_vals(ql)
            ql_lines.append(line)
        return ql_lines

    @staticmethod
    def set_quantitative_vals(test):
        # test -> quality.template
        QuantitativeLine = Pool().get('quality.quantitative.test.line')

        qt_lines = []
        for qt in test.quantitative_lines:
            line = QuantitativeLine()
            line.set_template_line_vals(qt)
            qt_lines.append(line)
        return qt_lines

    def apply_template_values(self):
        ql_lines = []
        qt_lines = []
        for template in self.templates:
            ql_lines += self.set_qualitative_vals(template)
            qt_lines += self.set_quantitative_vals(template)

        if ql_lines:
            self.qualitative_lines = ql_lines
        if qt_lines:
            self.quantitative_lines = qt_lines

    @classmethod
    @ModelView.button
    def apply_templates(cls, tests):
        for test in tests:
            test.apply_template_values()
            test.save()

    @classmethod
    def copy(cls, tests, default=None):
        if default is None:
            default = {}
        default.setdefault('number', None)
        if 'templates' not in default:
            default['templates'] = None
        return super(QualityTest, cls).copy(tests, default)

    @fields.depends('document')
    def on_change_document(self):
        pass


class QualitativeTestLine(sequence_ordered(), ModelSQL, ModelView):
    'Quality Qualitative Line'
    __name__ = 'quality.qualitative.test.line'

    test = fields.Many2One('quality.test', 'Test',
        ondelete='CASCADE')
    test_state = fields.Function(fields.Selection(_TEST_STATE, 'Test State'),
        'on_change_with_test_state')
    template_line = fields.Many2One('quality.qualitative.template.line',
        'Template Line')
    name = fields.Char('Name', required=True,
        states={
            'readonly': Bool(Eval('template_line', 0)),
            })
    proof = fields.Many2One('quality.proof', 'Proof', required=True, domain=[
            ('type', '=', 'qualitative'),
            ],
        states={
            'readonly': Bool(Eval('template_line', 0)),
            })
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof', -1)),
            ],
        states={
            'readonly': Bool(Eval('template_line', 0)),
            })
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    test_value = fields.Many2One('quality.qualitative.value', 'Test Value',
        required=True, domain=[
            ('method', '=', Eval('method', -1)),
            ],
        states={
            'readonly': Bool(Eval('template_line', 0)),
            })
    value = fields.Many2One('quality.qualitative.value', 'Value', domain=[
            ('method', '=', Eval('method', -1)),
            ])
    success = fields.Function(fields.Boolean('Success'), 'get_success')

    @fields.depends('proof')
    def on_change_proof(self):
        if not self.proof:
            self.method = None

    def get_success(self, name=None):
        if self.value == self.test_value:
            return True
        return False

    @fields.depends('test', '_parent_test.state')
    def on_change_with_test_state(self, name=None):
        return self.test and self.test.state or 'draft'

    def set_template_line_vals(self, template_line):
        self.template_line = template_line
        self.name = template_line.name
        self.proof = template_line.proof
        self.method = template_line.method
        self.internal_description = template_line.internal_description
        self.external_description = template_line.external_description
        self.test_value = template_line.valid_value
        self.sequence = template_line.sequence


class QuantitativeTestLine(sequence_ordered(), ModelSQL, ModelView):
    'Quality Quantitative Line'
    __name__ = 'quality.quantitative.test.line'

    test = fields.Many2One('quality.test', 'Test',
        ondelete='CASCADE', required=True)
    test_state = fields.Function(fields.Selection(_TEST_STATE, 'Test State'),
        'on_change_with_test_state')
    template_line = fields.Many2One('quality.quantitative.template.line',
        'Template Line', readonly=True)
    name = fields.Char('Name', required=True,
        states={
            'readonly': Bool(Eval('template_line', 0)),
            })
    proof = fields.Many2One('quality.proof', 'Proof', required=True, domain=[
            ('type', '=', 'quantitative'),
            ],
        states={
            'readonly': Bool(Eval('template_line', 0)),
            })
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof', -1)),
            ],
        states={
            'readonly': Bool(Eval('template_line', 0)),
            })
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    unit_range = fields.Many2One('product.uom', 'Unit Range', required=True,
        states={
            'readonly': Bool(Eval('template_line', 0)),
            })
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
        depends=['unit_range_digits'])
    max_value = fields.Float('Max Value',
        digits=(16, Eval('unit_range_digits', 2)), required=True,
        states={
            'readonly': Bool(Eval('template_line', 0)),
            },
        depends=['unit_range_digits'])
    value = fields.Float('Value', digits='unit')
    unit = fields.Many2One('product.uom', 'Unit',
        domain=[
            If(Bool(Eval('unit_range_category')),
                ('category', '=', Eval('unit_range_category')),
                ('category', '!=', -1)),
            ],
        states={
            'required': Bool(Eval('value')),
        })
    success = fields.Function(fields.Boolean('Success'), 'get_success')

    @fields.depends('test', '_parent_test.state')
    def on_change_with_test_state(self, name=None):
        return self.test and self.test.state or 'draft'

    @fields.depends('proof')
    def on_change_proof(self):
        if not self.proof:
            self.method = None

    @fields.depends('unit_range')
    def on_change_with_unit_range_digits(self, name=None):
        if not self.unit_range:
            return 2
        return self.unit_range.digits

    @fields.depends('unit_range')
    def on_change_with_unit_range_category(self, name=None):
        if self.unit_range:
            return self.unit_range.category.id

    @classmethod
    def get_success(self, lines, name):
        res = {}
        pool = Pool()
        Uom = pool.get('product.uom')
        for line in lines:
            res[line.id] = False
            value = line.value
            value = Uom.compute_qty(line.unit, value, line.unit_range)
            if (value is not None and
                    value >= line.min_value and value <= line.max_value):
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


class TestLine(UnionMixin, ModelSQL, ModelView, sequence_ordered()):
    'Quality Test Line'
    __name__ = 'quality.test.line'

    test = fields.Many2One('quality.test', 'Test', required=True)
    name = fields.Char('Name', required=True, translate=True)
    proof = fields.Many2One('quality.proof', 'Proof', required=True)
    method = fields.Many2One('quality.proof.method', 'Method', required=True,
        domain=[
            ('proof', '=', Eval('proof', -1)),
            ])
    type = fields.Selection('get_types', 'Type', required=True, readonly=True)
    internal_description = fields.Text('Internal Description')
    external_description = fields.Text('External Description')
    test_value = fields.Many2One('quality.qualitative.value', 'Test Value',
        required=True, readonly=True,
        domain=[
            ('method', '=', Eval('method', -1)),
            ])
    qualitative_value = fields.Many2One('quality.qualitative.value',
        'Qualitative Value',
        domain=[
            ('method', '=', Eval('method', -1)),
            ])
    quantitative_value = fields.Float('Quantitative Value', digits='unit')
    value = fields.Function(fields.Char('Value'), 'get_value')
    min_value = fields.Float('Min Value', digits='unit')
    max_value = fields.Float('Max Value', digits='unit')
    unit = fields.Many2One('product.uom', 'Unit')
    success = fields.Function(fields.Boolean('Success'), 'get_success')

    @staticmethod
    def union_models():
        return ['quality.qualitative.test.line',
            'quality.quantitative.test.line']

    @classmethod
    def get_types(cls):
        Model = Pool().get('ir.model')
        models = cls.union_models()
        models = Model.search([
                ('name', 'in', models),
                ])
        return [(m.name, m.string) for m in models]

    @classmethod
    def union_column(cls, name, field, table, Model):
        if name == 'type':
            return Model.__name__
        value = Literal(None)
        if name == 'quantitative_value':
            if 'quantitative' in Model.__name__:
                value = Column(table, 'value')
            return value
        if name == 'qualitative_value':
            if 'qualitative' in Model.__name__:
                value = Column(table, 'value')
            return value
        return super(TestLine, cls).union_column(name, field, table, Model)

    def get_value(self, name):
        value = ''
        if self.qualitative_value:
            value = self.qualitative_value.rec_name
        elif self.quantitative_value:
            value = str(self.quantitative_value)
        return value

    def get_success(self, name):
        record = self.union_unshard(self.id)
        return record.success

    @classmethod
    def write(cls, *args):
        pool = Pool()
        models_to_write = defaultdict(list)
        actions = iter(args)

        for models, values in zip(actions, actions):
            for model in models:
                record = cls.union_unshard(model.id)
                models_to_write[record.__name__].extend(([record], values))
        for model, arguments in models_to_write.items():
            Model = pool.get(model)
            Model.write(*arguments)

    @classmethod
    def delete(cls, lines):
        pool = Pool()
        models_to_delete = defaultdict(list)

        for model in lines:
            record = cls.union_unshard(model.id)
            models_to_delete[record.__name__].append(record)
        for model, records in models_to_delete.items():
            Model = pool.get(model)
            Model.delete(records)


class QualityTestQualityTemplate(ModelSQL):
    'Quality Test - Quality Template'
    __name__ = 'quality.test-quality.template'
    _table = 'quality_test_quality_template_rel'
    test = fields.Many2One('quality.test', 'Test', ondelete='CASCADE',
            required=True)
    template = fields.Many2One('quality.template', 'Quality Template',
        ondelete='CASCADE', required=True)

    @classmethod
    def __setup__(cls):
        super(QualityTestQualityTemplate, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('quality_test_uniq', Unique(t, t.test),
                'Quality Test can only be related with one template.'),
            ]
