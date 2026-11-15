import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,60,0))
w1=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-120/2).moveTo(47,49.5).box(13.5,13.5,12).union(w1.sketch().rect(120,200).push([(0,50)]).circle(29.5,mode='s').push([(0,-26)]).rect(15.5,11.5).finalize().extrude(-200)).union(w1.workplane(offset=-100/2).moveTo(52,96.5).box(6.5,3,6))