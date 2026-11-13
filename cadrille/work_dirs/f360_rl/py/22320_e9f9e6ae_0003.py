import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,27,0))
r=w0.sketch().segment((-100,-27),(-28,-100)).segment((73,-73.5)).segment((100,27)).segment((28,100)).segment((-73,73.5)).close().assemble().circle(45,mode='s').finalize().extrude(-53.5)