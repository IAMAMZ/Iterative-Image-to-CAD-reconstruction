import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,92))
w1=cq.Workplane('YZ',origin=(-17,0,0))
r=w0.workplane(offset=-37/2).moveTo(35,-56).cylinder(37,29.5).union(w0.sketch().arc((-7,70),(20,29),(19,-21)).segment((49,-21)).arc((85,42),(59.5,86)).segment((49,87)).segment((40,87)).segment((30,86)).close().assemble().finalize().extrude(-1.5)).union(w0.workplane(offset=8/2).moveTo(35,-56).cylinder(8,20)).union(w1.workplane(offset=-70/2).moveTo(-47,-95).cylinder(70,5)).union(w1.workplane(offset=-70/2).moveTo(-47,-95).box(6.5,4.5,70))