import cadquery as cq
w0=cq.Workplane('YZ',origin=(87,0,0))
w1=cq.Workplane('XY',origin=(0,0,0))
r=w0.sketch().push([(0,-5)]).circle(25).circle(19.5,mode='s').finalize().extrude(-187).union(w0.sketch().rect(63.5,71).rect(41.5,61,mode='s').finalize().extrude(-153)).union(w1.workplane(offset=35/2).moveTo(95,0).box(10,1.5,35)).union(w1.workplane(offset=6/2).moveTo(97,0.5).box(6,1.5,1))