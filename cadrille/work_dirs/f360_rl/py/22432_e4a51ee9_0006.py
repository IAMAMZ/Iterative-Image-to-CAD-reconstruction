import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,69))
r=w0.sketch().segment((-100,0),(-50,-87)).segment((50,-86.5)).segment((100,0)).segment((50,87)).segment((-50,86.5)).close().assemble().circle(64,mode='s').finalize().extrude(-137.5).union(w0.sketch().rect(96.5,173).circle(18.5,mode='s').finalize().extrude(-12.5))