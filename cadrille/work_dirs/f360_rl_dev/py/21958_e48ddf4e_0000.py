import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,3,0))
r=w0.sketch().segment((-95,-62),(22,-100)).segment((95,0)).segment((22,100)).segment((-95,62)).close().assemble().finalize().extrude(-6)