#This file is part of Tryton.  The COPYRIGHT file at the top level of this
#repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['Package', 'Move', 'Production', 'ShipmentOut']


class Package(metaclass=PoolMeta):
    __name__ = 'stock.package'

    @classmethod
    def __setup__(cls):
        super(Package, cls).__setup__()
        domains_to_remove = [
            ('shipment', '=', Eval('shipment')),
            ('to_location.type', 'in', ['customer', 'supplier']),
            ]
        for value in domains_to_remove:
            if value in cls.moves.domain:
                cls.moves.domain.remove(value)
                cls.moves.add_remove.append(value)


class Move(metaclass=PoolMeta):
    __name__ = 'stock.move'

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        if not cls.package.states:
            cls.package.states = {}
        cls.package.states.update({
                'readonly': ~Eval('context', {}).get('package_enabled', False),
                })


class Production(metaclass=PoolMeta):
    __name__ = 'production'

    @classmethod
    def __setup__(cls):
        super(Production, cls).__setup__()
        if not cls.outputs.context:
            cls.outputs.context = {}
        cls.outputs.context.update({
                'package_enabled': True,
                })


class ShipmentOut(metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'

    @classmethod
    def __setup__(cls):
        super(ShipmentOut, cls).__setup__()
        if not cls.inventory_moves.context:
            cls.inventory_moves.context = {}
        cls.inventory_moves.context.update({
                'package_enabled': True,
                })

    @classmethod
    def pack(cls, shipments):
        super(ShipmentOut, cls).pack(shipments)
        for shipment in shipments:
            outgoing_moves = {}
            for move in shipment.outgoing_moves:
                outgoing_moves.setdefault(move.product.id, [])
                outgoing_moves[move.product.id].append(move)
            for move in shipment.inventory_moves:
                if move.package:
                    for outmove in outgoing_moves[move.product.id]:
                        outmove.package = move.package
                        outmove.save()
                    if not move.package.shipment:
                        move.package.shipment = shipment
                        move.package.save()
