#!/usr/bin/python
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from pandac.PandaModules import PointLight

class FreeBLiTZ(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        self.stage = self.loader.loadModel('models/sandbox')
        self.stage.reparentTo(self.render)

        self.arm = Actor('models/blockchar')
        self.arm.reparentTo(self.stage)

        self.light = PointLight('plight')
        self.lightNP = self.stage.attachNewNode(self.light)
        self.lightNP.setPos(5, 5, 5)
        self.stage.setLight(self.lightNP)

app = FreeBLiTZ()
app.run()
