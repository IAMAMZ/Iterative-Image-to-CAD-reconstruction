import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-27))
r=w0.workplane(offset=21/2).cylinder(21,79.5).union(w0.sketch().segment((-86.5,-50),(0,-100)).segment((87,-50)).segment((86.5,50)).segment((0,100)).segment((-87,50)).close().assemble().circle(55,mode='s').finalize().extrude(54))