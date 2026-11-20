import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,6))
r=w0.sketch().circle(100).circle(91,mode='s').push([(0.5,-96)]).rect(3.5,6.5).finalize().extrude(-9.5)