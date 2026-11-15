import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
w1=cq.Workplane('YZ',origin=(-82,0,0))
r=w0.sketch().push([(0,29)]).circle(53).circle(48,mode='s').finalize().extrude(-200).union(w1.sketch().push([(-29,0)]).circle(43).circle(39,mode='s').finalize().extrude(76.5)).union(w1.workplane(offset=6/2).moveTo(97.5,0.5).box(3.5,1.5,1))