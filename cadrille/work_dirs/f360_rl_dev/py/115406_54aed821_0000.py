import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-65))
r=w0.workplane(offset=4/2).box(200,34.5,4).union(w0.sketch().segment((-100,-12),(64,-18.5)).segment((100,-12.5)).segment((100,18)).segment((-100,18)).close().assemble().rect(184.5,33,mode='s').finalize().extrude(130))