import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,21,0))
w1=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-17,-42),(100,-42)).segment((100,42)).segment((-17,43)).arc((-100,0),(-17,-42)).assemble().push([(-49,0)]).circle(41,mode='s').finalize().extrude(-42).union(w1.workplane(offset=119/2).moveTo(0.5,0.5).box(1.5,1.5,119)).union(w1.workplane(offset=2/2).moveTo(0.5,0.5).box(1.5,1.5,1))