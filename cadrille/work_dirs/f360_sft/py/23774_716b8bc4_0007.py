import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-23,0))
r=w0.sketch().circle(100).reset().face(w0.sketch().segment((-94,-10),(-82,-10)).arc((0,-83),(82,-10)).segment((94,-10)).segment((94,10)).segment((82,10)).arc((0,83),(-82,10)).segment((-94,10)).close().assemble(),mode='s').circle(64).finalize().extrude(46)