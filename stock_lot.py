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


class CreateQualityLotTestsMixin(object):
    __slots__ = ()

    @classmethod
    def create_lot_quality_tests(cls, documents, template):
        pool = Pool()
        QualityTest = pool.get('quality.test')
        StockLot = pool.get('stock.lot')
        lot_to_save = []

        for document in documents:
            lots = document.lots_for_quality_tests()
            if not lots:
                continue

            test_to_save = []
            with Transaction().set_context(_check_access=False):
                for lot in lots:
                    if lot.quality_tests:
                        continue

                    used_template = None
                    lot.active = False
                    lot_to_save.append(lot)

                    if not template:
                        continue
                    used_template = getattr(lot.product.template,
                        template + '_quality_template')
                    test = QualityTest(
                        test_date=datetime.now(),
                        templates=[used_template],
                        document=str(lot))
                    test.apply_template_values()
                    test_to_save.append(test)
                QualityTest.save(test_to_save)
        StockLot.save(lot_to_save)


class ShipmentIn(CreateQualityLotTestsMixin, metaclass=PoolMeta):
    __name__ = 'stock.shipment.in'

    @classmethod
    def receive(cls, shipments):
        super().receive(shipments)
        cls.create_lot_quality_tests(shipments, 'shipment_in')

    def lots_for_quality_tests(self):
        return list(set(m.lot for m in self.incoming_moves if m.lot and
            m.state == 'done' and
            m.product.template.shipment_in_quality_template and
            not [x for x in m.lot.quality_tests if
                m.product.template.shipment_in_quality_template in x]))


class ShipmentOut(CreateQualityLotTestsMixin, metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'

    @classmethod
    def pack(cls, shipments):
        super().pack(shipments)
        cls.create_lot_quality_tests(shipments, 'shipment_out')

    def lots_for_quality_tests(self):
        return list(set(m.lot for m in self.outgoing_moves if m.lot and
            m.state == 'draft' and
            m.product.template.shipment_out_quality_template and
            not [x for x in m.lot.quality_tests if
            m.product.template.shipment_out_quality_template in x]))


class Lot(metaclass=PoolMeta):
    __name__ = 'stock.lot'
    quality_tests = fields.One2Many('quality.test', 'document', 'Tests',
        readonly=True)

    @classmethod
    def copy(cls, lots, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['quality_tests'] = None
        return super().copy(lots, default)


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
