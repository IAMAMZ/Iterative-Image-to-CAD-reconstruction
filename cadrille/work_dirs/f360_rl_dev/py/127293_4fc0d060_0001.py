import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().segment((-100,-15),(75,-14.5)).segment((80,-11)).segment((84,-10)).segment((100,1)).segment((76,14.5)).segment((69,14.5)).segment((-70,14.5)).segment((-70.5,14)).segment((-100,15)).close().assemble().finalize().extrude(3)