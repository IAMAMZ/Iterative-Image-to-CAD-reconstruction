import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-23,0))
r=w0.sketch().circle(100).circle(44,mode='s').finalize().extrude(22).union(w0.sketch().arc((-67,-75),(10,-99),(69,-69.5)).segment((67.5,75.5)).arc((-1,99),(-69,75)).close().assemble().circle(44,mode='s').finalize().extrude(45))