import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,37,0))
r=w0.sketch().segment((-100,0),(-50,-87)).segment((50,-86.5)).segment((100,0)).segment((50,87)).segment((-50,86.5)).close().assemble().circle(58,mode='s').finalize().extrude(-73)