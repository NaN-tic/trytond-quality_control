# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.pool import Pool
from .configuration import *
from .quality import *
from .product import *

def register():
    Pool.register(
        Configuration,
        ConfigurationLine,
        Proof,
        ProofMethod,
        QualitativeValue,
        Template,
        QuantitativeTemplateLine,
        QualitativeTemplateLine,
        TemplateLine,
        QualityTest,
        QualitativeTestLine,
        QuantitativeTestLine,
        TestLine,
        QualityTestQualityTemplate,
        Product,
        ProductTemplate,
        TemplateQualityTemplate,
        ProductQualityTemplate,
        module='quality_control', type_='model')
