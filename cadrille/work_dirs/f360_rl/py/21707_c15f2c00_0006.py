import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-10,0))
r=w0.sketch().segment((-100,0),(-50,-87)).segment((50,-86.5)).segment((100,0)).segment((50,87)).segment((-5,86.5)).segment((-50,86.5)).close().assemble().finalize().extrude(10).union(w0.sketch().circle(74).circle(65.5,mode='s').circle(30).finalize().extrude(19.5))