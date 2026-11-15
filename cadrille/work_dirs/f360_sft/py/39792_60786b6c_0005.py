import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,25,0))
r=w0.workplane(offset=-50/2).moveTo(10,-70).cylinder(50,20).union(w0.sketch().arc((-40,74),(-8,13),(-20,-57)).arc((12,-100),(32,-49)).arc((34,31),(-16,92)).arc((-31,99),(-37,83)).arc((-39,79),(-40,74)).assemble().finalize().extrude(-10))