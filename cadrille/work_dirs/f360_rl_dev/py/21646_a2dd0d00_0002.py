import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,7,0))
r=w0.sketch().circle(100).circle(94.5,mode='s').circle(14).finalize().extrude(-14).union(w0.sketch().segment((-94,-6),(9,-12.5)).segment((9,6.5)).segment((-94,6)).close().assemble().finalize().extrude(-11.5))