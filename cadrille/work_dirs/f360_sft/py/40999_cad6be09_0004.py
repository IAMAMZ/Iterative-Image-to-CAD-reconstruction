import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-83,0))
r=w0.sketch().rect(200,200).push([(-7,29.5)]).rect(70,133,mode='s').finalize().extrude(166).union(w0.workplane(offset=167/2).box(142,70,167))