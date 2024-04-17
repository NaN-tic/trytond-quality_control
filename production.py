# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields
from .stock_lot import CreateQualityLotTestsMixin


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'
    production_quality_template = fields.Many2One('quality.template',
        'Production Quality Template')


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'


class Production(CreateQualityLotTestsMixin, metaclass=PoolMeta):
    __name__ = 'production'

    @classmethod
    def do(cls, productions):
        super().do(productions)
        cls.create_lot_quality_tests(productions, 'production')

    def lots_for_quality_tests(self):
        return list(set(m.lot for m in self.outputs if m.lot and
            m.state == 'done' and
            m.product.template.production_quality_template and
            not [x for x in m.lot.quality_tests if
            m.product.template.production_quality_template in x]))
