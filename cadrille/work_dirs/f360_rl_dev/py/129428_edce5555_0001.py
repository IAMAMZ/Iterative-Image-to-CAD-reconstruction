import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,13,0))
w1=cq.Workplane('ZX',origin=(0,21,0))
r=w0.sketch().push([(0,-88)]).circle(12).circle(8,mode='s').push([(0.5,-4.5)]).rect(15.5,149).finalize().extrude(-24).union(w1.sketch().push([(0,83)]).circle(17).circle(12,mode='s').finalize().extrude(-41.5))