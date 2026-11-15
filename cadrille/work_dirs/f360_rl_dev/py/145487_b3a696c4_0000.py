import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().rect(200,194.5).reset().face(w0.sketch().segment((-80,-49),(-39,-78)).segment((39,-77)).segment((80,-43.5)).segment((79,43)).segment((43,77)).segment((-39,77)).segment((-80,43)).close().assemble(),mode='s').circle(16.5).finalize().extrude(2.5)