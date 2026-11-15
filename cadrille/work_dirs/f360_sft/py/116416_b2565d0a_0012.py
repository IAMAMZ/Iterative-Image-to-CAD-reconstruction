import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-52,0))
r=w0.sketch().segment((-100,0),(-50,-87)).segment((50,-87)).segment((100,0)).segment((50,87)).segment((-50,87)).segment((-50,84)).segment((-50,78)).segment((-50,77)).close().assemble().circle(52,mode='s').finalize().extrude(104)