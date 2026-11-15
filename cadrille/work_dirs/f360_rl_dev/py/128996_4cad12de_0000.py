import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-61,0))
r=w0.sketch().segment((-92,-42),(-9,-100)).segment((83,-56)).segment((92,42)).segment((9,100)).segment((-83,56)).close().assemble().circle(34.5,mode='s').finalize().extrude(35).union(w0.sketch().circle(70).circle(34.5,mode='s').finalize().extrude(122))