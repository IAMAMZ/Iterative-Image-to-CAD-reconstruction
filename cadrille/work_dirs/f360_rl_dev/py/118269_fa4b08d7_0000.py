import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.workplane(offset=10/2).moveTo(-40.5,0).box(11.5,90,10).union(w0.sketch().segment((-46.5,-46),(46,-46)).segment((46,-34.5)).segment((-34,-35)).segment((-34.5,46)).segment((-46,46)).close().assemble().finalize().extrude(200))