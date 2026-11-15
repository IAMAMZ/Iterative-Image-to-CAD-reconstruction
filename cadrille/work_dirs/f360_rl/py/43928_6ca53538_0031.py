import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((8,-22),(9,-20)).arc((-6,0),(9,20)).segment((9,22)).arc((-10,3),(8,-22)).assemble().finalize().extrude(-200)