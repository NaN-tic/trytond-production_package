# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import stock


def register():
    Pool.register(
        stock.Package,
        stock.Move,
        stock.Production,
        stock.ShipmentOut,
        module='production_package', type_='model')
