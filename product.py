# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pyson import Eval 
from trytond.pool import PoolMeta

__all__ = ['Product', 'ProductTemplate',
    'TemplateQualityTemplate', 'ProductQualityTemplate']

__metaclass__ = PoolMeta

STATES = {
    'readonly': ~Eval('active', True),
}
DEPENDS = ['active']


class ProductTemplate:
    __name__ = "product.template"
    quality_controls = fields.Many2Many('product.template-quality.template',
        'template', 'quality', 'Quality Controls', states=STATES, depends=DEPENDS)


class Product:
    __name__ = "product.product"
    quality_controls = fields.Many2Many('product.product-quality.template',
        'product', 'quality', 'Quality Controls', states=STATES, depends=DEPENDS)


class TemplateQualityTemplate(ModelSQL):
    'Product Template - Quality Template'
    __name__ = 'product.template-quality.template'
    _table = 'product_template_quality_template_rel'
    template = fields.Many2One('product.template', 'Template', ondelete='CASCADE',
            required=True, select=True)
    quality = fields.Many2One('quality.template', 'Quality Template',
        ondelete='CASCADE', required=True, select=True)


class ProductQualityTemplate(ModelSQL):
    'Product - Quality Template'
    __name__ = 'product.product-quality.template'
    _table = 'product_product_quality_template_rel'
    product = fields.Many2One('product.product', 'Product', ondelete='CASCADE',
            required=True, select=True)
    quality = fields.Many2One('quality.template', 'Quality Template',
        ondelete='CASCADE', required=True, select=True)
