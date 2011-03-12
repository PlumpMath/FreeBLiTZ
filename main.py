#!/usr/bin/python
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor

class FreeBLiTZ(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        self.arm = Actor('armtest', {'walk': 'armtest-anim1'})
        self.arm.reparentTo(self.render)
        self.arm.loop('walk')

app = FreeBLiTZ()
app.run()
