# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.quality_control.tests.test_quality_control import suite
except ImportError:
    from .test_quality_control import suite

__all__ = ['suite']
