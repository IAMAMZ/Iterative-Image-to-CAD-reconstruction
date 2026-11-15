import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,25,0))
r=w0.sketch().arc((-17,-100),(12,-55),(15,-1)).segment((17,-1)).segment((17,100)).segment((0,100)).segment((0,11)).arc((-8,13),(-17,14)).close().assemble().finalize().extrude(-50)