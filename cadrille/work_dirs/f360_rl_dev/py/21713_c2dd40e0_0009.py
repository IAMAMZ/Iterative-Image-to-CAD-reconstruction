import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-11,0))
r=w0.sketch().segment((-24,-2),(3,-93)).arc((18,-99),(23,-85)).segment((0,-4)).segment((24,89)).arc((12,100),(0,88)).close().assemble().push([(13,-88)]).circle(5.5,mode='s').push([(12,90)]).circle(5.5).finalize().extrude(10.5).union(w0.workplane(offset=21/2).moveTo(-10,0).cylinder(21,4.5))