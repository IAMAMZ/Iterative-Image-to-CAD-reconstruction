import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-31))
w1=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-79,-16),(79,-16)).arc((67,8),(46,16)).segment((-46,16)).arc((-69,6),(-79,-14.5)).close().assemble().finalize().extrude(63).union(w1.workplane(offset=40/2).moveTo(0,-14.5).box(200,2.5,40)).union(w1.workplane(offset=8/2).moveTo(90,-13).box(7.5,1.5,1))