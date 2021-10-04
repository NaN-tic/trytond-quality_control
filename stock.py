# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta, Pool
from trytond.model import fields
from datetime import datetime
from trytond.transaction import Transaction


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    shipment_in_quality_template = fields.Many2One('quality.template',
        'Shipment In Quality Template')
    shipment_out_quality_template = fields.Many2One('quality.template',
        'Shipment Out Quality Template')


class CreateQualityModelTestsMixin(object):
    __slots__ = ()

    @classmethod
    def create_model_test(cls, shipments, type_, party_field):
        QualityTest = Pool().get('quality.test')
        if not shipments:
            return
        to_save = []
        with Transaction().set_context(_check_access=False):
            for shipment in shipments:
                party = getattr(shipment, party_field)
                used_template = getattr(party, type_ + '_quality_template')
                resource = str(shipment)
                test = QualityTest(
                    test_date=datetime.now(),
                    templates=[used_template],
                    document=resource)
                test.apply_template_values()
                to_save.append(test)

            QualityTest.save(to_save)


class ShipmentIn(CreateQualityModelTestsMixin, metaclass=PoolMeta):
    __name__ = 'stock.shipment.in'

    @classmethod
    def shipments_for_quality_test(cls, shipments):
        res = []
        for shipment in shipments:
            if shipment.supplier.shipment_in_quality_template:
                res.append(shipment)
        return res

    @classmethod
    def receive(cls, shipments):
        super().receive(shipments)
        to_test = cls.shipments_for_quality_test(shipments)
        cls.create_model_test(to_test, 'shipment_in', 'supplier')


class ShipmentOut(CreateQualityModelTestsMixin, metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'

    @classmethod
    def shipments_for_quality_test(cls, shipments):
        res = []
        for shipment in shipments:
            if shipment.customer.shipment_out_quality_template:
                res.append(shipment)
        return res

    @classmethod
    def pack(cls, shipments):
        super().pack(shipments)
        to_test = cls.shipments_for_quality_test(shipments)
        cls.create_model_test(to_test, 'shipment_out', 'customer')
