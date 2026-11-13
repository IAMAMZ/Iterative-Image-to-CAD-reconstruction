import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,19,0))
r=w0.sketch().rect(200,100).push([(-74.5,45)]).rect(3,2,mode='s').push([(76,-16)]).rect(2,12,mode='s').finalize().extrude(-38)