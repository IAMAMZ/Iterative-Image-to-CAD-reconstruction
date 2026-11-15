import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-63,-32),(63,-32)).segment((40,-17)).segment((43,16)).segment((63,31.5)).segment((62,32.5)).segment((-63,32.5)).close().assemble().finalize().extrude(-200)