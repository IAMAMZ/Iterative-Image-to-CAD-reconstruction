import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().segment((-22,19),(-22,44)).segment((-27,0)).segment((35,17)).segment((34,44.5)).segment((23,43)).arc((0,6),(-22,40)).close().assemble().finalize().extrude(39.5).union(w0.workplane(offset=200/2).moveTo(0,-38).box(200,11.5,200)).union(w0.workplane(offset=10/2).moveTo(97,-38.5).box(2.5,3.5,1))