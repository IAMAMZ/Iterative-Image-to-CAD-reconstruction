import cadquery as cq
w0=cq.Workplane('YZ',origin=(50,0,0))
r=w0.sketch().rect(100,200).push([(0,40)]).circle(19.5,mode='s').finalize().extrude(-100)