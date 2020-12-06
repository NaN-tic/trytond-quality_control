# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta, Pool
from trytond.model import fields, ModelView, Workflow
from datetime import datetime
from trytond.transaction import Transaction


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'
    shipment_in_quality_template = fields.Many2One('quality.template',
        'Shipment In Quality Template')
    shipment_out_quality_template = fields.Many2One('quality.template',
        'Shipment Out Quality Template')
    shipment_internal_quality_template = fields.Many2One('quality.template',
        'Shipment Internal Quality Template')

class CreateQualityLotTestsMixin(object):

    @classmethod
    def create_lot_quality_tests(cls, shipments, template):
        QualityTest = Pool().get('quality.test')
        StockLot = Pool().get('stock.lot')
        to_save = []
        to_create = []
        for shipment in shipments:
            lots = shipment.lots_for_quality_tests()
            if not lots:
                continue

            to_create = []
            today = datetime.today()
            for lot in lots:
                used_template = None
                lot.active = False
                to_save.append(lot)

                if not template:
                    continue

                used_template = getattr(lot.product.template,
                    template+'_quality_template')

                test_date = (datetime.combine(shipment.effective_date,
                    datetime.now().time()) if shipment.effective_date else
                    today)

                test = QualityTest(
                    test_date=test_date,
                    templates=[used_template],
                    document=str(lot))
                test.apply_template_values()
                to_create.append(test)

        with Transaction().set_user(0, set_context=True):
            QualityTest.save(to_create)

        StockLot.save(to_save)


class ShipmentIn(CreateQualityLotTestsMixin, metaclass=PoolMeta):
    __name__ = 'stock.shipment.in'

    @classmethod
    def receive(cls, shipments):
        super().receive(shipments)
        cls.create_lot_quality_tests(shipments, 'shipment_in')

    def lots_for_quality_tests(self):
        return list(set(m.lot for m in self.incoming_moves if m.lot and
            m.state == 'done' and
            m.product.template.shipment_in_quality_template))


class ShipmentOut(CreateQualityLotTestsMixin, metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'

    @classmethod
    def pack(cls, shipments):
        super().pack(shipments)
        cls.create_lot_quality_tests(shipments, 'shipment_out')

    def lots_for_quality_tests(self):
        return list(set(m.lot for m in self.outgoing_moves if m.lot and
            m.state == 'draft' and
            m.product.template.shipment_out_quality_template))


class ShipmentInternal(CreateQualityLotTestsMixin, metaclass=PoolMeta):
    __name__ = 'stock.shipment.internal'

    @classmethod
    def assign(cls, shipments):
        super().assign(shipments)
        cls.create_lot_quality_tests(shipments, 'shipment_internal')

    def lots_for_quality_tests(self):
        return list(set(m.lot for m in self.moves if m.lot and
            m.state == 'assigned' and
            m.product.template.shipment_internal_quality_template))


class Lot(metaclass=PoolMeta):
    __name__ = 'stock.lot'
    quality_tests = fields.One2Many('quality.test', 'document', 'Tests',
        readonly=True)


class QualityTest(metaclass=PoolMeta):
    __name__ = 'quality.test'

    @classmethod
    @ModelView.button
    def manager_validate(cls, tests):
        super().manager_validate(tests)
        cls.lot_active(tests)

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, tests):
        super().draft(tests)
        cls.lot_active(tests)

    @staticmethod
    def lot_active(tests):
        StockLot = Pool().get('stock.lot')
        to_save = []

        for test in tests:
            if isinstance(test.document, StockLot):
                test.document.active = False
                if test.state == 'successful':
                    test.document.active = True
                to_save.append(test.document)

        StockLot.save(to_save)
