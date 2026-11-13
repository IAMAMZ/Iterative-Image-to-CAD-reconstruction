import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
w1=cq.Workplane('ZX',origin=(0,-83.5,0))
r=w0.sketch().rect(166,200).push([(-16,-0)]).rect(65.5,65.5,mode='s').finalize().extrude(-200).union(w1.workplane(offset=166/2).moveTo(90.5,30.5).box(7,9.5,16))