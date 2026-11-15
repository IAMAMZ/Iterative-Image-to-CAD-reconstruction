import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,69))
r=w0.workplane(offset=-137.5/2).moveTo(0,0).box(113,200,137).union(w0.workplane(offset=-10/2).box(110.5,186.5,10))