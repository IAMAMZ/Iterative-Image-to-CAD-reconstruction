import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
w1=cq.Workplane('XY',origin=(0,0,91))
r=w0.sketch().arc((-10,-10),(10,0),(-10,10)).close().assemble().circle(7,mode='s').finalize().extrude(4).union(w1.sketch().segment((-47,-14),(47,-14)).segment((47,-6)).segment((37,-6)).segment((37,-13)).segment((-37,-13)).segment((-37,-6)).segment((-47,-6)).close().assemble().reset().face(w1.sketch().segment((-47,6),(-37,6)).segment((-37,13)).segment((37,13)).segment((37,6)).segment((47,6)).segment((47,14)).segment((-47,14)).close().assemble()).finalize().extrude(9))