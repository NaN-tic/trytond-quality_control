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

    >>> config = activate_modules(['stock_lot_deactivatable', 'quality_control'])

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

    >>> product_template.shipment_in_quality_template = template
    >>> product_template.shipment_out_quality_template = template
    >>> product_template.save()


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
    >>> Lot = Model.get('stock.lot')
    >>> lot = Lot()
    >>> lot.number = '1'
    >>> lot.product = product
    >>> lot.save()
    >>> move = shipment_in.incoming_moves.new()
    >>> move.product = product
    >>> move.uom = unit
    >>> move.quantity = 1
    >>> move.lot = lot
    >>> move.from_location = supplier_loc
    >>> move.to_location = input_loc
    >>> move.unit_price = Decimal('1')
    >>> shipment_in.save()

Receive products::

    >>> shipment_in.click('receive')
    >>> shipment_in.reload()
    >>> shipment_in.state
    'received'

Check the created Quality Tests::

    >>> QualityTest = Model.get('quality.test')
    >>> tests_in, = QualityTest.find([])
    >>> tests_in.document == lot
    True


Create Shipment out::

    >>> ShipmentOut = Model.get('stock.shipment.out')
    >>> shipment_out = ShipmentOut()
    >>> shipment_out.planned_date = today
    >>> shipment_out.customer = customer
    >>> shipment_out.warehouse = warehouse_loc
    >>> shipment_out.company = company

Add shipment lines of product 1::

    >>> StockMove = Model.get('stock.move')
    >>> shipment_out.outgoing_moves.extend([StockMove()])
    >>> for move in shipment_out.outgoing_moves:
    ...   move.product = product
    ...   move.lot = lot
    ...   move.uom = unit
    ...   move.quantity = 1
    ...   move.from_location = output_loc
    ...   move.to_location = customer_loc
    ...   move.unit_price = Decimal('1')
    ...   move.currency = company.currency
    >>> shipment_out.save()

Receive products::

    >>> a = shipment_out.click('assign_try')
    >>> shipment_out.reload()
    >>> shipment_out.click('pack')

Check the created Quality Tests::

    >>> QualityTest = Model.get('quality.test')
    >>> test_out, = QualityTest.find([])
    >>> test_out.document == lot
    True
