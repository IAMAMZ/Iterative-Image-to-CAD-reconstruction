import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-30,0))
r=w0.sketch().rect(200,100).circle(43,mode='s').finalize().extrude(40).union(w0.sketch().segment((-38,-10),(-4,-10)).segment((-4,-38)).segment((4,-38)).segment((4,-10)).segment((38,-10)).segment((38,10)).segment((4,10)).segment((4,38)).segment((-4,38)).segment((-4,10)).segment((-38,10)).close().assemble().finalize().extrude(61))