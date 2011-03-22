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

        # Character rig, which allows camera to follow character
        self.char_rig = self.stage.attachNewNode('char_rig')

        self.blockchar = Actor('models/blockchar')
        self.blockchar.reparentTo(self.char_rig)
        self.blockchar.setCompass()

        self.cam.reparentTo(self.char_rig)
        self.cam.setPos(2, -10, 7)
        self.cam.lookAt(2, 0, 7)

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
        self.taskMgr.add(self.MouseTask, 'MouseTask')

        self.move_speed = 0.3

    def move_forward(self):
        h = self.blockchar.getH()
        rig_h = self.char_rig.getH()
        self.blockchar.setH(self.avg_deg_sign(h, rig_h))
        self.char_rig.setPos(self.char_rig, 0, self.move_speed, 0)

    def move_left(self):
        h = self.blockchar.getH()
        rig_h = self.char_rig.getH()
        self.blockchar.setH(self.avg_deg_sign(h, (rig_h + 90)))
        self.char_rig.setPos(self.char_rig, -self.move_speed, 0, 0)

    def move_backward(self):
        h = self.blockchar.getH()
        rig_h = self.char_rig.getH()
        self.blockchar.setH(self.avg_deg_sign(h, (rig_h + 180)))
        self.char_rig.setPos(self.char_rig, 0, -self.move_speed, 0)

    def move_right(self):
        h = self.blockchar.getH()
        rig_h = self.char_rig.getH()
        self.blockchar.setH(self.avg_deg_sign(h, (rig_h - 90)))
        self.char_rig.setPos(self.char_rig, self.move_speed, 0, 0)

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

    def clamp_deg_sign(self, heading):
        return (heading + 180) % 360 - 180

    def avg_deg_sign(self, heading1, heading2):
        if heading2 - heading1 > 180:
            heading2 -= 360
        if heading2 - heading1 < -180:
            heading2 += 360
        return self.clamp_deg_sign(.85 * heading1 + .15 * heading2)

    def MouseTask(self, task):
        if self.mouseWatcherNode.hasMouse():
            (x, y) = self.mouseWatcherNode.getMouse()
            if self.prev_pos:
                if self.look or self.spin:
                    h_diff = (x - self.prev_pos[0]) * 180
                    p_diff = (y - self.prev_pos[1]) * 90
                    new_h = self.clamp_deg_sign(self.char_rig.getH() - h_diff)
                    self.char_rig.setH(new_h)
                    self.cam.setP(self.cam.getP() + p_diff)
                if self.spin:
                    char_new_h = self.avg_deg_sign(self.blockchar.getH(), new_h)
                    self.blockchar.setH(char_new_h)
            self.prev_pos = (x, y)
        return task.cont

app = FreeBLiTZ()
app.run()
