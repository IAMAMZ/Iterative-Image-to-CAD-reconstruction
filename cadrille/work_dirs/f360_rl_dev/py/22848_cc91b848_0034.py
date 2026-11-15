import cadquery as cq
w0=cq.Workplane('YZ',origin=(8,0,0))
r=w0.sketch().segment((-62,-46),(100,-92)).segment((100,92)).segment((-62,45)).arc((-100,1),(-62,-46)).assemble().push([(-53,0)]).circle(24,mode='s').finalize().extrude(-15)