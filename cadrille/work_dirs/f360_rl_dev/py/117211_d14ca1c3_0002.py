import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-80,-10),(80,-10)).segment((80,10)).segment((-62,10)).segment((-69,6)).segment((-73,9.5)).segment((-80,9)).close().assemble().finalize().extrude(-200)