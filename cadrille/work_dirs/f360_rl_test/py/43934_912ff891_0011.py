import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-15,0))
r=w0.sketch().rect(100,200).push([(0,67)]).circle(18.5,mode='s').push([(0,-67)]).circle(18,mode='s').finalize().extrude(28).union(w0.sketch().rect(90.5,200).circle(34.5,mode='s').finalize().extrude(29))