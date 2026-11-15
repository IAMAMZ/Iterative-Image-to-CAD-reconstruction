import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,15,0))
r=w0.sketch().circle(100).push([(-33,0)]).circle(15,mode='s').push([(-1,-50)]).circle(15,mode='s').push([(0,50)]).circle(15.5,mode='s').push([(33,0)]).circle(15.5,mode='s').finalize().extrude(-61).union(w0.sketch().circle(87).finalize().extrude(-16)).union(w0.sketch().circle(85).circle(62.5,mode='s').finalize().extrude(32))