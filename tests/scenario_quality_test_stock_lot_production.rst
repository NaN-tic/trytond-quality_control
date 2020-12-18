========================
Quality Control Scenario
========================

Imports::
    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()

Install quality_test module::

    >>> config = activate_modules(['production', 'stock_lot_deactivatable',
    ...   'quality_control'])

Create company::

    >>> _ = create_company()
    >>> company = get_company()


Create supplier::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> customer = Party(name='Customer')
    >>> customer.save()


Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> product_template = ProductTemplate()
    >>> product_template.name = 'product'
    >>> product_template.default_uom = unit
    >>> product_template.type = 'goods'
    >>> product_template.producible = True
    >>> product_template.list_price = Decimal('40')
    >>> product_template.save()
    >>> product, = product_template.products

Create Quality Configuration::

    >>> Sequence = Model.get('ir.sequence')
    >>> Configuration = Model.get('quality.configuration')
    >>> IrModel = Model.get('ir.model')
    >>> sequence, = Sequence.find([('code', '=', 'quality.test')])
    >>> configuration = Configuration(1)
    >>> config_line = configuration.allowed_documents.new()
    >>> config_line.quality_sequence = sequence
    >>> allowed_doc, = IrModel.find([('model','=','stock.lot')])
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
    >>> qt_line.internal_description = 'quality line intenal description'
    >>> qt_line.external_description = 'quality line external description'
    >>> qt_line.min_value = Decimal('1.00')
    >>> qt_line.max_value = Decimal('2.00')
    >>> template.quantitative_lines.append(qt_line)
    >>> template.save()
    >>> template.reload()

Assign Template to Product::

    >>> product_template.production_quality_template = template
    >>> product_template.save()


Get stock locations and create new internal location::

    >>> Location = Model.get('stock.location')
    >>> warehouse_loc, = Location.find([('code', '=', 'WH')])
    >>> supplier_loc, = Location.find([('code', '=', 'SUP')])
    >>> customer_loc, = Location.find([('code', '=', 'CUS')])
    >>> input_loc, = Location.find([('code', '=', 'IN')])
    >>> output_loc, = Location.find([('code', '=', 'OUT')])
    >>> storage_loc, = Location.find([('code', '=', 'STO')])
    >>> production_loc, = Location.find([('code', '=', 'PROD')])
    >>> internal_loc = Location()
    >>> internal_loc.name = 'Internal Location'
    >>> internal_loc.code = 'INT'
    >>> internal_loc.type = 'storage'
    >>> internal_loc.parent = storage_loc
    >>> internal_loc.save()


Make a production::

    >>> Lot = Model.get('stock.lot')
    >>> lot = Lot()
    >>> lot.number = '1'
    >>> lot.product = product
    >>> lot.save()
    >>> StockMove = Model.get('stock.move')
    >>> Production = Model.get('production')
    >>> production = Production()
    >>> production.planned_date = today
    >>> production.product = product
    >>> production.quantity = 2
    >>> production.outputs.extend([StockMove()])
    >>> for move in production.outputs:
    ...   move.product = product
    ...   move.lot = lot
    ...   move.uom = unit
    ...   move.quantity = 1
    ...   move.from_location = production_loc
    ...   move.to_location = storage_loc
    ...   move.unit_price = Decimal('1')
    ...   move.currency = company.currency
    >>> production.save()
    >>> production.click('wait')
    >>> a = production.click('assign_try')
    >>> production.click('run')
    >>> production.click('done')

Check the created Quality Tests::

    >>> QualityTest = Model.get('quality.test')
    >>> test, = QualityTest.find([])
    >>> test.document == lot
    True
