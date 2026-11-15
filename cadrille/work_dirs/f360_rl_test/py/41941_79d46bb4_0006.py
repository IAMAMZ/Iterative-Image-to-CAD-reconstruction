import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,4,0))
r=w0.sketch().segment((-100,-67),(100,-100)).segment((100,-60)).segment((-27,-45)).segment((-24,-17)).segment((6,-2)).segment((-29,33.5)).segment((0,46)).segment((100,66.5)).segment((100,100)).segment((-10,80)).segment((-100,67)).segment((-100,30)).segment((-68,0)).segment((-100,-39)).close().assemble().finalize().extrude(-7)