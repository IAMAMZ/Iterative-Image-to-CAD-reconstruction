import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,2,0))
r=w0.sketch().rect(36.5,200).push([(0,-82)]).rect(28,28.5,mode='s').push([(0,0)]).rect(26.5,63.5,mode='s').push([(0,82)]).rect(28,28.5,mode='s').finalize().extrude(-5.5)