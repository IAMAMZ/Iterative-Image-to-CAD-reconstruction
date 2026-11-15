import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().segment((-86,-2),(-44,-77)).segment((44,-73)).segment((86,2)).segment((44,77)).segment((-44,73)).close().assemble().finalize().extrude(50).union(w0.sketch().segment((-40,0),(-23,-35)).segment((20,-37)).segment((40,-2)).segment((26,35)).segment((-20,35)).close().assemble().finalize().extrude(200))