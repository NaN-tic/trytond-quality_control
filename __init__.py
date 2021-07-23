# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import quality
from . import stock
from . import stock_lot
from . import production


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationLine,
        quality.Proof,
        quality.ProofMethod,
        quality.QualitativeValue,
        quality.Template,
        quality.QuantitativeTemplateLine,
        quality.QualitativeTemplateLine,
        quality.TemplateLine,
        quality.QualityTest,
        quality.QualitativeTestLine,
        quality.QuantitativeTestLine,
        quality.TestLine,
        quality.QualityTestQualityTemplate,
        module='quality_control', type_='model')
    Pool.register(
        stock_lot.Template,
        stock_lot.ShipmentIn,
        stock_lot.ShipmentOut,
        stock_lot.Lot,
        stock_lot.QualityTest,
        depends=['stock_lot_deactivatable'],
        module='quality_control', type_='model')
    Pool.register(
        stock.Party,
        stock.ShipmentIn,
        stock.ShipmentOut,
        depends=['stock'],
        module='quality_control', type_='model')
    Pool.register(
        production.Template,
        production.Production,
        depends=['production', 'stock_lot_deactivatable'],
        module='quality_control', type_='model')
