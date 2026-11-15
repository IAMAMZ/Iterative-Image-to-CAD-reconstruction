import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,73))
r=w0.workplane(offset=-173/2).cylinder(173,14.5).union(w0.workplane(offset=-130/2).cylinder(130,16.5)).union(w0.sketch().circle(48).push([(-0,30)]).circle(8.5,mode='s').finalize().extrude(27))