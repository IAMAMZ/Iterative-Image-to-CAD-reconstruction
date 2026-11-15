import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().arc((-26,68),(3,-100),(22,70)).arc((20,85),(13,98)).segment((-19,100)).arc((-22,84),(-26,68)).assemble().push([(0,-13)]).circle(4,mode='s').finalize().extrude(14)