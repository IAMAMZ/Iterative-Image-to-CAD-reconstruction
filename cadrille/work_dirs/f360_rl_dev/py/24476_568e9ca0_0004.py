import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
w1=cq.Workplane('YZ',origin=(-45,0,0))
r=w0.sketch().segment((-73,-25),(-40,-25)).segment((-47,-8)).segment((-52,17)).segment((-57,25)).segment((-73,25)).arc((-100,2),(-73,-25)).assemble().push([(-76,0)]).circle(13.5,mode='s').finalize().extrude(-14).union(w1.workplane(offset=145/2).moveTo(-17,0).cylinder(145,7.5)).union(w1.workplane(offset=145/2).moveTo(-17,0).box(6.5,1.5,145))