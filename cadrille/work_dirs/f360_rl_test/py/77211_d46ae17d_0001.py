import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-50,-29),(0,-57)).segment((50,-29)).segment((50,29)).segment((0,57)).segment((-50,29)).close().assemble().finalize().extrude(-200)