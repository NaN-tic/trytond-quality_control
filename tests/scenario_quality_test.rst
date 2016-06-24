========================
Quality Control Scenario
========================

Imports::
    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install quality_test module::

    >>> Module = Model.get('ir.module.module')
    >>> quality_test_module, = Module.find(
    ...     [('name', '=', 'quality_control')])
    >>> Module.install([quality_test_module.id], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='US Dollar', symbol=u'$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[]',
    ...         mon_decimal_point='.')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find([])

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.list_price = Decimal('40')
    >>> template.cost_price = Decimal('25')
    >>> template.save()
    >>> product.template = template
    >>> product.save()

Create Quality Configuration::

    >>> Sequence = Model.get('ir.sequence')
    >>> sequence = Sequence.find([('code','=','quality.test')])[0]
    >>> Configuration = Model.get('quality.configuration')
    >>> configuration = Configuration()
    >>> configuration.name = 'Configuration'
    >>> Product = Model.get('product.product')
    >>> ConfigLine = Model.get('quality.configuration.line')
    >>> config_line = ConfigLine()
    >>> configuration.allowed_documents.append(config_line)
    >>> config_line.quality_sequence = sequence
    >>> models = Model.get('ir.model')
    >>> allowed_doc, = models.find([('model','=','product.product')])
    >>> config_line.document = allowed_doc
    >>> configuration.save()

Create Qualitative Proof::

    >>> Proof = Model.get('quality.proof')
    >>> QualityValue = Model.get('quality.qualitative.value')
    >>> Method = Model.get('quality.proof.method')
    >>> val1 = QualityValue(name='Val1')
    >>> val2 = QualityValue(name='Val2')
    >>> qlproof = Proof(name='Qualitative Proof', type='qualitative')
    >>> method1 = Method(name='Method 1')
    >>> qlproof.methods.append(method1)
    >>> method1.possible_values.append(val1)
    >>> method1.possible_values.append(val2)
    >>> qlproof.save()


Create Quantitative Proof::

    >>> Proof = Model.get('quality.proof')
    >>> Method = Model.get('quality.proof.method')
    >>> qtproof = Proof(name='Quantitative Proof', type='quantitative')
    >>> method2 = Method(name='Method 2')
    >>> qtproof.methods.append(method2)
    >>> qtproof.save()

Look For Values::

    >>> method1, = Method.find([('name', '=', 'Method 1')])
    >>> method2, = Method.find([('name', '=', 'Method 2')])
    >>> val1, = QualityValue.find([('name','=','Val1')])
    >>> val2, = QualityValue.find([('name','=','Val2')])

Create Template, Template1::

    >>> Template = Model.get('quality.template')
    >>> template=Template()
    >>> template.name = 'Template 1'
    >>> template.document = product
    >>> template.internal_description='Internal description'
    >>> template.external_description='External description'
    >>> QlTemplateLine = Model.get('quality.qualitative.template.line')
    >>> ql_line = QlTemplateLine()
    >>> template.qualitative_lines.append(ql_line)
    >>> ql_line.name = 'Line1'
    >>> ql_line.sequence = 1
    >>> ql_line.proof = qlproof
    >>> ql_line.method = method1
    >>> ql_line.valid_value = val1
    >>> ql_line.internal_description = 'quality line intenal description'
    >>> ql_line.external_description = 'quality line external description'
    >>> QtTemplateLine = Model.get('quality.quantitative.template.line')
    >>> qt_line = QtTemplateLine()
    >>> qt_line.name = 'Quantitative Line'
    >>> qt_line.sequence = 1
    >>> qt_line.proof = qtproof
    >>> qt_line.method = method2
    >>> qt_line.unit = unit
    >>> qt_line.unit_range = unit
    >>> qt_line.internal_description = 'quality line intenal description'
    >>> qt_line.external_description = 'quality line external description'
    >>> qt_line.min_value = Decimal('1.00')
    >>> qt_line.max_value = Decimal('2.00')
    >>> template.quantitative_lines.append(qt_line)
    >>> template.save()
    >>> template.reload()

Create and assign template to Test::

    >>> Test = Model.get('quality.test')
    >>> test=Test()
    >>> test.name = 'TEST/'
    >>> test.document = product
    >>> test.templates.append(template)
    >>> test.save()
    >>> Test.apply_templates([test.id], config.context)

Check Unsuccess on Test Line::

    >>> test.reload()
    >>> test.qualitative_lines[0].success
    False
    >>> test.quantitative_lines[0].success
    False
    >>> test.success
    False

Check Success on Test Line::

    >>> test.qualitative_lines[0].value = val1
    >>> test.quantitative_lines[0].value = Decimal('1.00')
    >>> test.quantitative_lines[0].unit = unit
    >>> test.save()
    >>> test.qualitative_lines[0].success
    True
    >>> test.quantitative_lines[0].success
    True
    >>> test.success
    True

Confirm Test::

    >>> test.save()
    >>> test.state
    u'draft'
    >>> Test.confirmed([test.id], config.context)
    >>> test.reload()
    >>> test.state
    u'confirmed'

Validate "successful" Test::

    >>> Test.manager_validate([test.id], config.context)
    >>> test.reload()
    >>> test.state
    u'successful'

Set To Draft Test::

    >>> Test.draft([test.id], config.context)
    >>> test.reload()
    >>> test.state
    u'draft'

Modify test to check failed test::

    >>> test.quantitative_lines[0].value = Decimal('12')
    >>> test.save()
    >>> Test.confirmed([test.id], config.context)
    >>> Test.manager_validate([test.id], config.context)
    >>> test.reload()
    >>> test.state
    u'failed'
