import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().segment((-61,-95),(-55,-100)).segment((-8,-23)).segment((15,-4)).segment((61,79)).segment((60,100)).segment((-8,0)).close().assemble().push([(13,10)]).circle(5,mode='s').finalize().extrude(2.5)