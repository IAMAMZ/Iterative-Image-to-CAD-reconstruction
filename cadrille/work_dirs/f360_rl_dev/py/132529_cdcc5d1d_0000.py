import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,22))
r=w0.workplane(offset=-43/2).moveTo(0,-36).box(1,2,43).union(w0.workplane(offset=-32/2).moveTo(0,36.5).box(1,1.5,32)).union(w0.sketch().segment((-100,-37),(-59,-37)).segment((29,-37)).segment((100,-37)).segment((100,38)).segment((-59,38)).segment((-100,38)).close().assemble().finalize().extrude(-32))