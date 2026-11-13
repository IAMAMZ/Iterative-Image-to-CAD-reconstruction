import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-34,0))
r=w0.sketch().push([(56,0)]).rect(88,124).push([(56.5,0)]).rect(73,116,mode='s').finalize().extrude(8).union(w0.sketch().push([(-38,0)]).rect(124,124).push([(-38,-1)]).circle(28,mode='s').finalize().extrude(69))