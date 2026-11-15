import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-75,0))
r=w0.workplane(offset=71/2).box(182.5,142.5,71).union(w0.sketch().rect(200,150).push([(0,-9)]).circle(36.5,mode='s').finalize().extrude(150))