import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,23,0))
r=w0.sketch().segment((-100,-20),(50,-20)).segment((79,-14)).segment((100,-2)).segment((100,6)).segment((56,19.5)).segment((46.5,20)).segment((-7,19.5)).segment((-79,18.5)).segment((-100,18.5)).close().assemble().finalize().extrude(-46.5)