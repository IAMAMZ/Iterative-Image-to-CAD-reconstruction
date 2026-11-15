import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,64.5))
w1=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().rect(200,77.5).rect(90.5,17,mode='s').finalize().extrude(-128.5).union(w1.workplane(offset=-2/2).box(1.5,1.5,1))