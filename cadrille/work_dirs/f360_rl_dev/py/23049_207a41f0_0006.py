import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,71))
r=w0.workplane(offset=-171/2).cylinder(171,47.5).union(w0.sketch().segment((-67,-38),(0,-77)).segment((67,-38)).segment((66.5,38)).segment((0,77)).segment((-67,37.5)).close().assemble().finalize().extrude(29))