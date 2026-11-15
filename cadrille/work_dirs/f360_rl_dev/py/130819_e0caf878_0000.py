import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-63,-26),(63,-26)).segment((63,-22)).segment((-60,-22)).segment((-60,22)).segment((63,22)).segment((63,26)).segment((-63,26)).close().assemble().finalize().extrude(-200)