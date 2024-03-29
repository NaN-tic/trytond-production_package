===========================
Production Package Scenario
===========================

=============
General Setup
=============

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()

Activate production_package::

    >>> config = activate_modules('production_package')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create customer::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Configuration production location::

    >>> Location = Model.get('stock.location')
    >>> warehouse, = Location.find([('code', '=', 'WH')])
    >>> production_location, = Location.find([('code', '=', 'PROD')])
    >>> warehouse.production_location = production_location
    >>> warehouse.save()
    >>> supplier_loc, = Location.find([('code', '=', 'SUP')])
    >>> customer_loc, = Location.find([('code', '=', 'CUS')])
    >>> output_loc, = Location.find([('code', '=', 'OUT')])
    >>> storage_loc, = Location.find([('code', '=', 'STO')])

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.producible = True
    >>> template.list_price = Decimal(30)
    >>> template.save()
    >>> product, = template.products

Create Package type::

    >>> PackageType = Model.get('stock.package.type')
    >>> package_type = PackageType(name='Box')
    >>> package_type.save()

Create Components::

    >>> template1 = ProductTemplate()
    >>> template1.name = 'component 1'
    >>> template1.default_uom = unit
    >>> template1.type = 'goods'
    >>> template1.list_price = Decimal(5)
    >>> template1.save()
    >>> component1, = template1.products

    >>> meter, = ProductUom.find([('symbol', '=', 'm')])
    >>> centimeter, = ProductUom.find([('symbol', '=', 'cm')])
    >>> template2 = ProductTemplate()
    >>> template2.name = 'component 2'
    >>> template2.default_uom = meter
    >>> template2.type = 'goods'
    >>> template2.list_price = Decimal(7)
    >>> template2.save()
    >>> component2, = template2.products

Create Bill of Material::

    >>> BOM = Model.get('production.bom')
    >>> BOMInput = Model.get('production.bom.input')
    >>> BOMOutput = Model.get('production.bom.output')
    >>> bom = BOM(name='product')
    >>> input1 = BOMInput()
    >>> bom.inputs.append(input1)
    >>> input1.product = component1
    >>> input1.quantity = 5
    >>> input2 = BOMInput()
    >>> bom.inputs.append(input2)
    >>> input2.product = component2
    >>> input2.quantity = 150
    >>> input2.uom = centimeter
    >>> output = BOMOutput()
    >>> bom.outputs.append(output)
    >>> output.product = product
    >>> output.quantity = 1
    >>> bom.save()

    >>> ProductBom = Model.get('product.product-production.bom')
    >>> product.boms.append(ProductBom(bom=bom))
    >>> product.save()

Create an Inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> InventoryLine = Model.get('stock.inventory.line')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory_line1 = InventoryLine()
    >>> inventory.lines.append(inventory_line1)
    >>> inventory_line1.product = component1
    >>> inventory_line1.quantity = 10
    >>> inventory_line2 = InventoryLine()
    >>> inventory.lines.append(inventory_line2)
    >>> inventory_line2.product = component2
    >>> inventory_line2.quantity = 5
    >>> inventory.save()
    >>> Inventory.confirm([inventory.id], config.context)
    >>> inventory.state
    'done'

Make a production and pack it's outputs::

    >>> Production = Model.get('production')
    >>> Package = Model.get('stock.package')
    >>> package = Package(type=package_type)
    >>> package.save()
    >>> production = Production()
    >>> production.product = product
    >>> production.bom = bom
    >>> production.quantity = 2
    >>> output, = production.outputs
    >>> output.package == None
    True
    >>> output.package = package
    >>> production.save()
    >>> Production.wait([production.id], config.context)
    >>> Production.assign_try([production.id], config.context)
    True
    >>> Production.run([production.id], config.context)
    >>> Production.done([production.id], config.context)
    >>> production.reload()
    >>> output, = production.outputs
    >>> output.package == package
    True

Make a pre-packaged shipment of the produced products::

    >>> ShipmentOut = Model.get('stock.shipment.out')
    >>> StockMove = Model.get('stock.move')
    >>> shipment_out = ShipmentOut()
    >>> shipment_out.planned_date = today
    >>> shipment_out.customer = customer
    >>> shipment_out.warehouse = warehouse
    >>> shipment_out.company = company
    >>> move = StockMove()
    >>> shipment_out.outgoing_moves.append(move)
    >>> move.product = product
    >>> move.uom =unit
    >>> move.quantity = 2
    >>> move.from_location = output_loc
    >>> move.to_location = customer_loc
    >>> move.company = company
    >>> move.unit_price = Decimal('1')
    >>> move.currency = company.currency
    >>> shipment_out.save()
    >>> ShipmentOut.wait([shipment_out.id], config.context)
    >>> shipment_out.reload()
    >>> shipment_out.inventory_moves[0].package == None
    True
    >>> shipment_out.outgoing_moves[0].package == None
    True
    >>> inventory_move, = shipment_out.inventory_moves
    >>> inventory_move.package = package
    >>> inventory_move.save()
    >>> ShipmentOut.assign_try([shipment_out.id], config.context)
    True
    >>> ShipmentOut.pack([shipment_out.id], config.context)
    >>> shipment_out.reload()
    >>> inventory_move, = shipment_out.inventory_moves
    >>> outgoing_move, = shipment_out.outgoing_moves
    >>> inventory_move.package == package
    True
    >>> outgoing_move.package == inventory_move.package
    True
    >>> package.reload()
    >>> package.shipment == shipment_out
    True
