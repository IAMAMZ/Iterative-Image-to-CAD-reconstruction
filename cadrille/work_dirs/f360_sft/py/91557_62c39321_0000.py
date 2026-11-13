import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-21,0))
r=w0.workplane(offset=13/2).cylinder(13,98).union(w0.sketch().arc((-21,34),(-41,-13),(2,-42)).arc((41,11),(-21,34)).assemble().finalize().extrude(42))