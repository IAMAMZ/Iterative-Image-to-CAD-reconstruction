import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.workplane(offset=-200/2).cylinder(200,18).union(w0.sketch().arc((-23,7),(-18,-14),(1,-24)).segment((23,-7)).segment((23,14)).arc((10,20),(-3,24)).arc((-11,13),(-23,7)).assemble().finalize().extrude(-16))