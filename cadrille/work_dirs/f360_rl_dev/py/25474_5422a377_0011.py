import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-8,0))
r=w0.sketch().circle(100).push([(-84,0)]).circle(4,mode='s').push([(0,0)]).circle(16.5,mode='s').finalize().extrude(3.5).union(w0.sketch().circle(66).circle(16.5,mode='s').finalize().extrude(15))