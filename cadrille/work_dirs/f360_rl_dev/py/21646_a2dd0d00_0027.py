import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,11,0))
r=w0.sketch().circle(100).circle(91.5,mode='s').push([(-42.5,-0)]).rect(99.5,14.5).push([(0,0)]).circle(11.5).finalize().extrude(-20)