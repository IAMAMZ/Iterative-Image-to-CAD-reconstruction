import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,57,0))
r=w0.sketch().segment((-97,-34),(-21,-100)).segment((76,-68)).segment((97,34)).segment((21,100)).segment((-76,68)).close().assemble().circle(56.5,mode='s').finalize().extrude(-114)