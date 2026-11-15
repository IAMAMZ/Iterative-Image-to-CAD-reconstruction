import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,46))
w1=cq.Workplane('YZ',origin=(86,0,0))
r=w0.sketch().segment((-100,-46),(47,-46)).segment((47,46)).segment((-69.5,46)).segment((-100,46)).close().assemble().push([(-26,0)]).circle(28,mode='s').finalize().extrude(-92).union(w1.workplane(offset=14/2).cylinder(14,55))