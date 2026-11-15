import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,33,0))
r=w0.sketch().arc((-100,32),(-91,-1),(-100,-34)).arc((100,1),(-100,32)).assemble().reset().face(w0.sketch().arc((-60,1),(-49,-36),(-21,-63)).arc((81,38),(-60,1)).assemble(),mode='s').finalize().extrude(-67).union(w0.workplane(offset=-5/2).moveTo(1,1).cylinder(5,40))