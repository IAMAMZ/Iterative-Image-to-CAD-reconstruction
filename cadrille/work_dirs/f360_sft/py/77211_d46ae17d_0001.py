import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-51,-29),(-1,-58)).segment((5,-48)).segment((51,-29)).segment((51,29)).segment((1,58)).segment((-51,29)).close().assemble().finalize().extrude(-200)