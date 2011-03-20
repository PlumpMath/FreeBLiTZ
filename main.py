#!/usr/bin/python
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from pandac.PandaModules import PointLight
from pandac.PandaModules import loadPrcFileData
loadPrcFileData('', 'win-size 960 600')

class FreeBLiTZ(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        self.stage = self.loader.loadModel('models/sandbox')
        self.stage.reparentTo(self.render)

        self.blockchar = Actor('models/blockchar')
        self.blockchar.reparentTo(self.stage)

        base.cam.reparentTo(self.blockchar)
        base.cam.setPos(2, -10, 7)

        self.light = PointLight('plight')
        self.lightNP = self.stage.attachNewNode(self.light)
        self.lightNP.setPos(5, 5, 5)
        self.stage.setLight(self.lightNP)

        self.accept('w', self.move_forward)
        self.accept('a', self.move_left)
        self.accept('s', self.move_backward)
        self.accept('d', self.move_right)
        self.accept('w-repeat', self.move_forward)
        self.accept('a-repeat', self.move_left)
        self.accept('s-repeat', self.move_backward)
        self.accept('d-repeat', self.move_right)
        self.accept('mouse2', self.begin_look)
        self.accept('mouse2-up', self.end_look)
        self.accept('mouse3', self.begin_spin)
        self.accept('mouse3-up', self.end_spin)

        self.spin = False
        self.look = False
        self.prev_pos = None
        self.cam_angle = 3.14159
        self.taskMgr.add(self.MouseTask, 'MouseTask')

    def move_forward(self):
        self.blockchar.setFluidPos(self.blockchar, 0, 0.2, 0)
        self.cam_angle = self.cam_angle * .95 + 3.14159 * .05

    def move_left(self):
        self.blockchar.setFluidPos(self.blockchar, -0.2, 0, 0)

    def move_backward(self):
        self.blockchar.setFluidPos(self.blockchar, 0, -0.2, 0)
        self.cam_angle = self.cam_angle * .95 + 3.14159 * .05

    def move_right(self):
        self.blockchar.setFluidPos(self.blockchar, 0.2, 0, 0)

    def begin_spin(self):
        self.spin = True

    def end_spin(self):
        self.spin = False
        self.prev_pos = None

    def begin_look(self):
        self.look = True

    def end_look(self):
        self.look = False
        self.prev_pos = None

    def MouseTask(self, task):
        from math import sin, cos
        if self.mouseWatcherNode.hasMouse():
            (x, y) = self.mouseWatcherNode.getMouse()
            if self.prev_pos:
                if self.spin:
                    self.blockchar.setH(self.blockchar, (self.prev_pos[0] - x) * 180)
                    self.cam.setP(self.cam, (y - self.prev_pos[1]) * 90)
                elif self.look:
                    self.cam_angle = self.cam_angle - (self.prev_pos[0] - x) * 10
                    if self.cam_angle >= 3.14159 * 2:
                        self.cam_angle -= 3.14159 * 2
                    if self.cam_angle <= 0:
                        self.cam_angle += 3.14159 * 2
            print self.cam_angle
            self.cam.setPos(sin(self.cam_angle) * 10, cos(self.cam_angle) * 10, 7)
            self.cam.lookAt(2, 0, 7)
            if self.prev_pos:
                if self.look:
                    self.cam.setP((y) * 90)
            self.prev_pos = (x, y)
        return task.cont

app = FreeBLiTZ()
app.run()
