import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-53))
r=w0.workplane(offset=-47/2).cylinder(47,17.5).union(w0.workplane(offset=-10/2).cylinder(10,24)).union(w0.workplane(offset=153/2).cylinder(153,17.5)).union(w0.workplane(offset=-7/2).box(1.5,1.5,1))