#!/usr/bin/python
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from pandac.PandaModules import PointLight
from pandac.PandaModules import loadPrcFileData
loadPrcFileData('', 'win-size 960 600')
loadPrcFileData('', 'interpolate-frames 1')

class FreeBLiTZ(ShowBase):

    def __init__(self):
        from pandac.PandaModules import CollisionNode, CollisionRay, CollisionSphere, CollisionTraverser, BitMask32
        from pandac.PandaModules import CollisionHandlerFloor, CollisionHandlerPusher, CollisionHandlerEvent
        ShowBase.__init__(self)

        FLOOR_MASK = BitMask32(1)
        OBSTACLE_MASK = BitMask32(2)
        ZONE_MASK = BitMask32(4)

        self.stage = self.loader.loadModel('models/sandbox3')
        self.floor = self.stage.find('**/=CollideType=floor')
        self.floor.setCollideMask(FLOOR_MASK)
        self.obstacles = self.stage.find('**/=CollideType=obstacle')
        self.obstacles.setCollideMask(OBSTACLE_MASK)
        self.zones = self.stage.find('**/=CollideType=zone')
        self.zones.setCollideMask(ZONE_MASK)
        self.stage.reparentTo(self.render)

        # Character rig, which allows camera to follow character
        self.char_rig = self.stage.attachNewNode('char_rig')

        self.blockchar = Actor('models/robot3', {'run': 'models/robot3-run'})
        self.blockchar.setPlayRate(2.0, 'run')
        self.blockchar.reparentTo(self.char_rig)
        self.blockchar.setCompass()
        self.blockchar.setCollideMask(0)
        self.blockchar_from_floor = self.blockchar.attachNewNode(CollisionNode('blockchar_floor'))
        self.blockchar_from_floor.node().addSolid(CollisionRay(0, 0, 0.1, 0, 0, -10))
        self.blockchar_from_floor.node().setCollideMask(0)
        self.blockchar_from_floor.node().setFromCollideMask(FLOOR_MASK)
        self.blockchar_from_obstacle = self.blockchar.attachNewNode(CollisionNode('blockchar_obstacle'))
        self.blockchar_from_obstacle.node().addSolid(CollisionSphere(0, 0, 0.85, 0.85))
        self.blockchar_from_obstacle.node().setCollideMask(0)
        self.blockchar_from_obstacle.node().setFromCollideMask(OBSTACLE_MASK)
        self.blockchar_from_zone = self.blockchar.attachNewNode(CollisionNode('blockchar_zone'))
        self.blockchar_from_zone.node().addSolid(CollisionSphere(0, 0, 0.55, 0.55))
        self.blockchar_from_zone.node().setCollideMask(0)
        self.blockchar_from_zone.node().setFromCollideMask(ZONE_MASK)

        self.cam.reparentTo(self.char_rig)
        self.cam.setPos(0.5, -3, 1.5)
        self.cam.lookAt(0.5, 0, 1.5)

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

        self.floor_handler = CollisionHandlerFloor()
        self.floor_handler.addCollider(self.blockchar_from_floor, self.char_rig)
        self.wall_handler = CollisionHandlerPusher()
        self.wall_handler.addCollider(self.blockchar_from_obstacle, self.char_rig)
        self.zone_handler = CollisionHandlerEvent()
        self.zone_handler.addInPattern('%fn-into-%in')
        self.zone_handler.addOutPattern('%fn-out-%in')
        def foo(entry):
            print 'You are in the zone'
        def bar(entry):
            print 'You are not in the zone'
        self.accept('blockchar_zone-into-Cube', foo)
        self.accept('blockchar_zone-out-Cube', bar)
        self.cTrav = CollisionTraverser('main traverser')
        self.cTrav.addCollider(self.blockchar_from_floor, self.floor_handler)
        self.cTrav.addCollider(self.blockchar_from_obstacle, self.wall_handler)
        self.cTrav.addCollider(self.blockchar_from_zone, self.zone_handler)
        #self.cTrav.showCollisions(self.stage)

    def begin_forward(self):
        self.move_forward = True
        self.blockchar.loop('run')

    def begin_left(self):
        self.move_left = True
        self.blockchar.loop('run')

    def begin_backward(self):
        self.move_backward = True
        self.blockchar.loop('run')

    def begin_right(self):
        self.move_right = True
        self.blockchar.loop('run')

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
            self.cTrav.traverse(self.stage)
            self.moving = True
            self.char_rig.setPos(self.char_rig, *vector)
        else:
            self.blockchar.stop()
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
