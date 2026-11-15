import cadquery as cq
w0=cq.Workplane('YZ',origin=(15,0,0))
r=w0.sketch().rect(100,200).push([(0,-69.5)]).rect(22,1,mode='s').push([(0,69.5)]).rect(22,1,mode='s').finalize().extrude(-30)