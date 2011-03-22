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
        self.cam.setPos(2, -14, 7)
        self.cam.lookAt(2, 0, 7)

        self.light = PointLight('plight')
        self.lightNP = self.stage.attachNewNode(self.light)
        self.lightNP.setPos(5, 5, 5)
        self.stage.setLight(self.lightNP)

        self.move_forward = False
        self.move_left = False
        self.move_backward = False
        self.move_right = False
        self.moving = False
        self.move_prev_time = None
        self.accept('w', self.begin_forward)
        self.accept('a', self.begin_left)
        self.accept('s', self.begin_backward)
        self.accept('d', self.begin_right)
        self.accept('w-up', self.end_forward)
        self.accept('a-up', self.end_left)
        self.accept('s-up', self.end_backward)
        self.accept('d-up', self.end_right)
        self.taskMgr.add(self.MoveTask, 'MoveTask')

        self.spin = False
        self.look = False
        self.prev_pos = None
        self.accept('mouse2', self.begin_look)
        self.accept('mouse2-up', self.end_look)
        self.accept('mouse3', self.begin_spin)
        self.accept('mouse3-up', self.end_spin)
        self.taskMgr.add(self.MouseTask, 'MouseTask')

        # Based on a jogging speed of 6mph
        self.move_speed = 2.7 # m/s

    def begin_forward(self):
        self.move_forward = True

    def begin_left(self):
        self.move_left = True

    def begin_backward(self):
        self.move_backward = True

    def begin_right(self):
        self.move_right = True

    def end_forward(self):
        self.move_forward = False

    def end_left(self):
        self.move_left = False

    def end_backward(self):
        self.move_backward = False

    def end_right(self):
        self.move_right = False

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

    def MoveTask(self, task):
        keys = 0
        if self.move_left ^ self.move_right:
            keys += 1
        if self.move_backward ^ self.move_forward:
            keys += 1
        self.moving = False
        if keys and self.move_prev_time:
            heading = 0
            if self.move_left and not self.move_right:
                heading += 90
            elif self.move_right and not self.move_left:
                heading -= 90
            if self.move_backward and not self.move_forward:
                if self.move_left and not self.move_right:
                    heading += 180
                else:
                    heading -= 180
            elif self.move_forward and not self.move_backward:
                heading += 0
            heading /= keys

            speed = self.move_speed * (task.time - self.move_prev_time)
            if heading % 90 == 45:
                speed = 0.70710678118654746 * speed

            # TODO: Scale Blender models instead of scaling movement speed.
            # Scale movement speed as if a blender unit were 1 meter
            speed *= 8 / 1.7

            if heading == 0:
                vector = (0, speed, 0)
            elif heading == 45:
                vector = (-speed, speed, 0)
            elif heading == 90:
                vector = (-speed, 0, 0)
            elif heading == 135:
                vector = (-speed, -speed, 0)
            elif heading == -45:
                vector = (speed, speed, 0)
            elif heading == -90:
                vector = (speed, 0, 0)
            elif heading == -135:
                vector = (speed, -speed, 0)
            elif heading == -180:
                vector = (0, -speed, 0)

            h = self.blockchar.getH()
            rig_h = self.char_rig.getH()
            self.blockchar.setH(self.avg_deg_sign(h, rig_h + heading))
            self.moving = True
            self.char_rig.setPos(self.char_rig, *vector)
        self.move_prev_time = task.time
        return task.cont

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
                if self.spin and not self.moving:
                    char_new_h = self.avg_deg_sign(self.blockchar.getH(), new_h)
                    self.blockchar.setH(char_new_h)
            self.prev_pos = (x, y)
        return task.cont

app = FreeBLiTZ()
app.run()
