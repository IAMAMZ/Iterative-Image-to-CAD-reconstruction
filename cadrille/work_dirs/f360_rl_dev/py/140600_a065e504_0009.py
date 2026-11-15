import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-65))
w1=cq.Workplane('YZ',origin=(-4.5,0,0))
r=w0.sketch().segment((-95,30),(-19,-21)).arc((95,26),(-12,85)).segment((-19,82)).close().assemble().push([(20,29)]).circle(66.5,mode='s').finalize().extrude(1.5).union(w0.workplane(offset=129/2).moveTo(26,-99).box(2,2,129)).union(w0.workplane(offset=129/2).moveTo(26,38.5).box(2,1,129)).union(w1.workplane(offset=60/2).moveTo(-97.5,61.5).box(5,7,60)).union(w1.workplane(offset=1/2).moveTo(37.5,62.5).box(4.5,3.5,1))