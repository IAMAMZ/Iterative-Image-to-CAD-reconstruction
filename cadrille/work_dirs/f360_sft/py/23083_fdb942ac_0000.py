import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-28,0))
w1=cq.Workplane('YZ',origin=(10,0,0))
r=w0.sketch().arc((-99,-29),(-89,-46),(-70,-50)).segment((83,-50)).arc((97,-27),(99,1)).segment((99,35)).arc((89,46),(76,50)).segment((-83,50)).segment((-99,35)).close().assemble().finalize().extrude(-13).union(w0.sketch().push([(-43,0)]).circle(35).circle(33,mode='s').finalize().extrude(15)).union(w0.sketch().push([(-43,0)]).circle(13).push([(14.5,0)]).rect(5,40).finalize().extrude(68)).union(w1.sketch().arc((39,11),(41,14),(39,17)).close().assemble().finalize().extrude(-2))