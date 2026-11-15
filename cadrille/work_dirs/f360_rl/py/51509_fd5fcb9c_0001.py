import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,5,0))
r=w0.sketch().arc((-96,-1),(-7,-100),(96,-43)).segment((66,-44)).arc((-67,0),(66,44)).segment((96,43.5)).arc((-10,99),(-96,1)).close().assemble().finalize().extrude(-10)