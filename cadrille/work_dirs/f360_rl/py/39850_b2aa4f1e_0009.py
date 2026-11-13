import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,20))
r=w0.sketch().segment((-100,-40),(63,-40)).segment((79,-33)).segment((79,31)).segment((100,39)).segment((96.5,40)).segment((20,40)).segment((20,-29.5)).segment((-100,-29)).close().assemble().finalize().extrude(-40)