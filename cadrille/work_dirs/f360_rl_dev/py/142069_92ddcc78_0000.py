import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
w1=cq.Workplane('YZ',origin=(-48,0,0))
r=w0.sketch().segment((19,25),(48,33.5)).segment((20,35)).close().assemble().finalize().extrude(-94).union(w0.sketch().segment((-48,-32),(-46,-35)).segment((-19,-19)).segment((-21,-17)).close().assemble().finalize().extrude(-3.5)).union(w1.sketch().segment((-37,-100),(-29,-100)).segment((-37,-94)).close().assemble().finalize().extrude(16)).union(w1.workplane(offset=2/2).moveTo(35,98.5).box(2.5,3,1))