import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,10))
r=w0.sketch().segment((-69,-100),(69,-100)).segment((69,32)).segment((0,100)).segment((-69,31)).close().assemble().finalize().extrude(-19)