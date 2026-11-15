import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().segment((-100,2),(-95,-5)).segment((98,-5)).segment((100,5)).segment((-94,5)).close().assemble().finalize().extrude(2)