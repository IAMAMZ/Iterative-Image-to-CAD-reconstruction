import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,28,0))
r=w0.sketch().segment((-12,-100),(-1,-91)).segment((12,-99)).segment((27,-98)).segment((39,-92)).arc((98,19),(0,99)).arc((-99,12),(-12,-100)).assemble().finalize().extrude(-56)