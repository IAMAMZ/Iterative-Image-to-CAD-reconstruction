import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,39,0))
w1=cq.Workplane('ZX',origin=(0,73,0))
r=w0.sketch().arc((-30,6),(0,-100),(27,7)).segment((27,73)).segment((-30,73.5)).close().assemble().push([(0,-41)]).circle(31.5,mode='s').finalize().extrude(-78).union(w1.workplane(offset=-146/2).moveTo(0,85.5).box(118,29,146)).union(w1.workplane(offset=-10/2).moveTo(0,85.5).box(1.5,1.5,10))