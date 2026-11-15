import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,67))
r=w0.workplane(offset=-167/2).box(182,96,167).union(w0.sketch().arc((10,-21),(26,0),(10,21)).close().assemble().finalize().extrude(29)).union(w0.sketch().push([(-35,0)]).circle(48).circle(23,mode='s').push([(10,3)]).circle(14,mode='s').finalize().extrude(33))