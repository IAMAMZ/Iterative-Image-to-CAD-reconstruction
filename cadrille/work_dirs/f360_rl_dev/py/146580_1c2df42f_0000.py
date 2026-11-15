import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,67))
r=w0.workplane(offset=-133.5/2).moveTo(0,0).box(133.5,200,133).union(w0.workplane(offset=-79/2).box(129.5,182.5,79)).union(w0.workplane(offset=-19/2).box(129.5,186.5,19))