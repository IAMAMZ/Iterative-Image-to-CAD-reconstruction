import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,5,0))
r=w0.sketch().arc((66,-43),(-67,12),(71,41)).arc((84,44),(96,42)).arc((-95,1),(95,-43)).arc((82,-46),(69,-43)).close().assemble().finalize().extrude(-10)