# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields, ModelSingleton
from trytond.transaction import Transaction

__all__ = ['Configuration', 'ConfigurationLine']


class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Quality configuration'
    __name__ = 'quality.configuration'

    allowed_documents = fields.One2Many('quality.configuration.line',
        'configuration', 'Documents with Quality Control')


class ConfigurationLine(ModelSQL, ModelView):
    'Quality Configuration Model'
    __name__ = 'quality.configuration.line'

    company = fields.Many2One('company.company', 'Company', required=True,
        select=True)
    quality_sequence = fields.Many2One('ir.sequence',
            'Quality Sequence', domain=[('code', '=', 'quality.test')],
            required=True)
    document = fields.Many2One('ir.model', 'Document', required=True)
    configuration = fields.Many2One('quality.configuration', 'Configuration')

    @staticmethod
    def default_company():
        """ Return default company value, context setted for company field """
        return Transaction().context.get('company')
