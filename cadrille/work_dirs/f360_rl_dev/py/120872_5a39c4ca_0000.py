import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-0))
r=w0.sketch().segment((-14,45),(-8,40)).segment((-8,-46)).segment((9,-100)).segment((0,11)).segment((8,29.5)).segment((14,45.5)).segment((8,54.5)).segment((8,100)).segment((0,100)).segment((0,56.5)).segment((-9,50.5)).close().assemble().finalize().extrude(1)