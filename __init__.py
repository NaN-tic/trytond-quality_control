# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import quality


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
