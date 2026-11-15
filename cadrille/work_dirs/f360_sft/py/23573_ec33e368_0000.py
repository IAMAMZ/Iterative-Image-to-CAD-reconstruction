import cadquery as cq
w0=cq.Workplane('YZ',origin=(-63,0,0))
w1=cq.Workplane('YZ',origin=(11,0,0))
r=w0.sketch().circle(100).circle(90,mode='s').finalize().extrude(127).union(w1.sketch().arc((-55,-71),(-47,-77),(-40,-84)).segment((40,-84)).segment((40,-71)).close().assemble().finalize().extrude(-11))