import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().circle(100).circle(81,mode='s').finalize().extrude(-200).union(w0.workplane(offset=-100/2).cylinder(100,99)).union(w0.workplane(offset=-10/2).cylinder(10,8))