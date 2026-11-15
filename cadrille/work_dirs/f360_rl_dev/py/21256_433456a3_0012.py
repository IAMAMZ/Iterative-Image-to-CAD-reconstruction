import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
w1=cq.Workplane('XY',origin=(0,0,11))
r=w0.sketch().segment((-100,50),(-92,-29)).segment((-69,-31)).segment((-70,0)).segment((-83.5,49.5)).segment((-89,56.5)).segment((-95,53)).close().assemble().reset().face(w0.sketch().segment((-59,-49),(0,-50)).segment((100,-46.5)).segment((93,-27)).segment((83,-28)).segment((80,-32)).segment((-50,-33.5)).segment((-59,-36)).close().assemble()).finalize().extrude(-12).union(w1.workplane(offset=-22/2).moveTo(-83,-41).cylinder(22,15.5)).union(w1.workplane(offset=-12/2).moveTo(97.5,-41.5).box(1,7.5,12))