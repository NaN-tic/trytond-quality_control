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

    >>> config = activate_modules(['stock', 'quality_control'])

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
    >>> Product = Model.get('product.product')
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('40')
    >>> template.save()
    >>> product, = template.products

Create Quality Configuration::

    >>> Sequence = Model.get('ir.sequence')
    >>> Configuration = Model.get('quality.configuration')
    >>> IrModel = Model.get('ir.model')
    >>> sequence, = Sequence.find([('name', '=', 'Quality Control')])
    >>> configuration = Configuration(1)
    >>> config_line = configuration.allowed_documents.new()
    >>> config_line.quality_sequence = sequence
    >>> allowed_doc, = IrModel.find([('model','=','stock.shipment.in')])
    >>> config_line.document = allowed_doc
    >>> config_line = configuration.allowed_documents.new()
    >>> config_line.quality_sequence = sequence
    >>> allowed_doc2, = IrModel.find([('model','=','stock.shipment.out')])
    >>> config_line.document = allowed_doc2
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

Assign Template to Supplier::

    >>> supplier.shipment_in_quality_template = template
    >>> supplier.save()
    >>> customer.shipment_out_quality_template = template
    >>> customer.save()


Get stock locations and create new internal location::

    >>> Location = Model.get('stock.location')
    >>> warehouse_loc, = Location.find([('code', '=', 'WH')])
    >>> supplier_loc, = Location.find([('code', '=', 'SUP')])
    >>> customer_loc, = Location.find([('code', '=', 'CUS')])
    >>> input_loc, = Location.find([('code', '=', 'IN')])
    >>> output_loc, = Location.find([('code', '=', 'OUT')])
    >>> storage_loc, = Location.find([('code', '=', 'STO')])
    >>> internal_loc = Location()
    >>> internal_loc.name = 'Internal Location'
    >>> internal_loc.code = 'INT'
    >>> internal_loc.type = 'storage'
    >>> internal_loc.parent = storage_loc
    >>> internal_loc.save()

Create Shipment In::

    >>> ShipmentIn = Model.get('stock.shipment.in')
    >>> shipment_in = ShipmentIn()
    >>> shipment_in.planned_date = today
    >>> shipment_in.supplier = supplier
    >>> shipment_in.warehouse = warehouse_loc

Add three shipment lines of product 1::

    >>> StockMove = Model.get('stock.move')
    >>> move = shipment_in.incoming_moves.new()
    >>> move.product = product
    >>> move.uom = unit
    >>> move.quantity = 1
    >>> move.from_location = supplier_loc
    >>> move.to_location = input_loc
    >>> move.unit_price = Decimal('1')
    >>> move.currency = company.currency
    >>> shipment_in.save()

Receive products::

    >>> ShipmentIn.receive([shipment_in.id], config.context)
    >>> shipment_in.reload()
    >>> shipment_in.state
    'received'

Check the created Quality Tests::

    >>> QualityTest = Model.get('quality.test')
    >>> tests_in, = QualityTest.find([])
    >>> tests_in.document == shipment_in
    True

Create Shipment out::

    >>> ShipmentOut = Model.get('stock.shipment.out')
    >>> shipment_out = ShipmentOut()
    >>> shipment_out.planned_date = today
    >>> shipment_out.customer = customer
    >>> shipment_out.warehouse = warehouse_loc

Add three shipment lines of product 1::

    >>> StockMove = Model.get('stock.move')
    >>> move = shipment_out.outgoing_moves.new()
    >>> move.product = product
    >>> move.uom = unit
    >>> move.quantity = 1
    >>> move.from_location = supplier_loc
    >>> move.to_location = input_loc
    >>> move.unit_price = Decimal('1')
    >>> move.currency = company.currency
    >>> shipment_out.save()

Receive products::

    >>> shipment_out.click('wait')
    >>> a = shipment_out.click('assign_try')
    >>> shipment_out.reload()
    >>> shipment_out.click('pack')


Check the created Quality Tests::

    >>> QualityTest = Model.get('quality.test')
    >>> tests_in, test_out = QualityTest.find([])
    >>> test_out.document == shipment_out
    True
