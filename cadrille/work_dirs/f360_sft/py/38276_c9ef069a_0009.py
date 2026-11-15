import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-26))
r=w0.sketch().segment((-100,1),(-49,-86)).segment((50,-86)).segment((100,1)).segment((50,86)).segment((-50,86)).close().assemble().circle(44,mode='s').finalize().extrude(52)