#!/usr/bin/python
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.actor.Actor import Actor
from pandac.PandaModules import loadPrcFileData, BitMask32
loadPrcFileData('', 'win-size 960 600')
loadPrcFileData('', 'interpolate-frames 1')
loadPrcFileData('', 'notify-level-collide debug')

FLOOR_MASK = BitMask32(1)
OBSTACLE_MASK = BitMask32(2)
ZONE_MASK = BitMask32(4)

def clamp_deg_sign(heading):
    return (heading + 180) % 360 - 180

def avg_deg_sign(heading1, heading2):
    if heading2 - heading1 > 180:
        heading2 -= 360
    if heading2 - heading1 < -180:
        heading2 += 360
    return clamp_deg_sign(.85 * heading1 + .15 * heading2)


class Character(DirectObject):
    def __init__(self, name, char_rig):
        from pandac.PandaModules import CollisionNode, CollisionRay, CollisionSphere
        self.name = name
        self.char_rig = char_rig
        self.actor = Actor('models/robot3', {'run': 'models/robot3-run'})
        self.actor.setPlayRate(2.0, 'run')
        self.actor.reparentTo(self.char_rig)
        self.actor.setCompass()
        self.actor.setCollideMask(0)
        self.actor_from_floor = self.actor.attachNewNode(CollisionNode('blockchar_floor'))
        self.actor_from_floor.node().addSolid(CollisionRay(0, 0, 0.25, 0, 0, -10))
        self.actor_from_floor.node().setCollideMask(0)
        self.actor_from_floor.node().setFromCollideMask(FLOOR_MASK)
        self.actor_from_obstacle = self.actor.attachNewNode(CollisionNode('blockchar_obstacle'))
        self.actor_from_obstacle.node().addSolid(CollisionSphere(0, 0, 0.35, 0.35))
        self.actor_from_obstacle.node().setCollideMask(0)
        self.actor_from_obstacle.node().setFromCollideMask(OBSTACLE_MASK)
        self.actor_from_zone = self.actor.attachNewNode(CollisionNode('blockchar_zone'))
        self.actor_from_zone.node().addSolid(CollisionSphere(0, 0, 0.55, 0.55))
        self.actor_from_zone.node().setCollideMask(0)
        self.actor_from_zone.node().setFromCollideMask(ZONE_MASK)
        self.move_forward = False
        self.move_left = False
        self.move_backward = False
        self.move_right = False
        self.moving = False
        self.spinning = False
        self.move_prev_time = None
        # Based on a jogging speed of 6mph
        self.move_speed = 2.7 # m/s

    def begin_forward(self):
        self.move_forward = True
        self.actor.loop('run')

    def begin_left(self):
        self.move_left = True
        self.actor.loop('run')

    def begin_backward(self):
        self.move_backward = True
        self.actor.loop('run')

    def begin_right(self):
        self.move_right = True
        self.actor.loop('run')

    def end_forward(self):
        self.move_forward = False

    def end_left(self):
        self.move_left = False

    def end_backward(self):
        self.move_backward = False

    def end_right(self):
        self.move_right = False

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

            h = self.actor.getH()
            rig_h = self.char_rig.getH()
            self.actor.setH(avg_deg_sign(h, rig_h + heading))
            self.moving = True
            self.char_rig.setFluidPos(self.char_rig, *vector)
            print 'POSITION SET'
        else:
            self.actor.stop()
        self.move_prev_time = task.time
        return task.cont

    def begin_spin(self):
        self.spinning = True

    def end_spin(self):
        self.spinning = False
        self.prev_pos = None

    def spin(self, new_h):
        if self.spinning and not self.moving:
            char_new_h = avg_deg_sign(self.actor.getH(), new_h)
            self.actor.setH(char_new_h)


class FreeBLiTZ(ShowBase):

    def __init__(self):
        from pandac.PandaModules import CollisionHandlerFloor, CollisionHandlerPusher, CollisionHandlerEvent, CollisionTraverser
        from pandac.PandaModules import DirectionalLight, AmbientLight, VBase4
        ShowBase.__init__(self)

        self.sky = self.loader.loadModel('models/sky-sphere')
        self.sky.reparentTo(self.render)
        self.stage = self.loader.loadModel('models/test-collide')
        self.stage.reparentTo(self.render)
        self.floor = self.stage.findAllMatches('**/=CollideType=floor')
        self.floor.setCollideMask(FLOOR_MASK)
        self.obstacles = self.stage.findAllMatches('**/=CollideType=obstacle')
        if self.obstacles:
            self.obstacles.setCollideMask(OBSTACLE_MASK)
        self.zones = self.stage.findAllMatches('**/=CollideType=zone')
        if self.zones:
            self.zones.setCollideMask(ZONE_MASK)
        self.create_stanchions()

        # Character rig, which allows camera to follow character
        self.char_rig = self.stage.attachNewNode('char_rig')

        self.active_char = Character('mainchar', self.char_rig)

        self.cam.reparentTo(self.char_rig)
        self.cam.setPos(0.5, -3, 1.5)
        self.cam.lookAt(0.5, 0, 1.5)

        self.light = DirectionalLight('dlight')
        self.light.setColor(VBase4(0.3, 0.28, 0.26, 1.0))
        self.lightNP = self.stage.attachNewNode(self.light)
        self.lightNP.setHpr(-75, -45, 0)
        self.stage.setLight(self.lightNP)

        self.amblight = AmbientLight('amblight')
        self.amblight.setColor(VBase4(0.7, 0.68, 0.66, 1.0))
        self.amblightNP = self.stage.attachNewNode(self.amblight)
        self.stage.setLight(self.amblightNP)

        self.accept('w', self.active_char.begin_forward)
        self.accept('a', self.active_char.begin_left)
        self.accept('s', self.active_char.begin_backward)
        self.accept('d', self.active_char.begin_right)
        self.accept('w-up', self.active_char.end_forward)
        self.accept('a-up', self.active_char.end_left)
        self.accept('s-up', self.active_char.end_backward)
        self.accept('d-up', self.active_char.end_right)
        self.taskMgr.add(self.active_char.MoveTask, 'MoveTask')

        self.look = False
        self.prev_pos = None
        self.accept('mouse2', self.begin_look)
        self.accept('mouse2-up', self.end_look)
        self.accept('mouse3', self.active_char.begin_spin)
        self.accept('mouse3-up', self.active_char.end_spin)
        self.taskMgr.add(self.MouseTask, 'MouseTask')

        self.floor_handler = CollisionHandlerFloor()
        self.floor_handler.addCollider(self.active_char.actor_from_floor, self.char_rig)
        self.wall_handler = CollisionHandlerPusher()
        self.wall_handler.addCollider(self.active_char.actor_from_obstacle, self.char_rig)
        self.zone_handler = CollisionHandlerEvent()
        self.zone_handler.addInPattern('%fn-into')
        self.zone_handler.addOutPattern('%fn-out')
        def foo(entry):
            print 'You are in the zone'
        def bar(entry):
            print 'You are not in the zone'
        self.accept('blockchar_zone-into', foo)
        self.accept('blockchar_zone-out', bar)
        self.cTrav = CollisionTraverser('main traverser')
        self.cTrav.setRespectPrevTransform(True)
        self.cTrav.addCollider(self.active_char.actor_from_floor, self.floor_handler)
        self.cTrav.addCollider(self.active_char.actor_from_obstacle, self.wall_handler)
        self.cTrav.addCollider(self.active_char.actor_from_zone, self.zone_handler)
        #self.cTrav.showCollisions(self.stage)

    def create_stanchions(self):
        from pandac.PandaModules import GeomVertexReader, CollisionNode, CollisionTube
        self.stanchions = self.stage.findAllMatches('**/=Stanchion')
        for stanchion in self.stanchions:
            geomnode = stanchion.node()
            radius = float(stanchion.getTag('Stanchion'))
            geom = geomnode.getGeom(0)
            vdata = geom.getVertexData()
            for gp in range(geom.getNumPrimitives()):
                vreader = GeomVertexReader(vdata, 'vertex')
                prim = geom.getPrimitive(gp)
                prim = prim.decompose()
                for p in range(prim.getNumPrimitives()):
                    start = prim.getPrimitiveStart(p)
                    end = prim.getPrimitiveEnd(p)
                    vertices = []
                    for v in range(start, end):
                        vi = prim.getVertex(v)
                        vreader.setRow(vi)
                        vertex = vreader.getData3f()
                        vertices.append(vertex)
                    vertices.append(vertices[0])
                    for i in range(1, len(vertices)):
                        a, b =  vertices[i-1], vertices[i]
                        stanchion_np = stanchion.attachNewNode(CollisionNode('stanchion'))
                        print 'creating cyl with radius %f from %s to %s' % (radius, a, b)
                        stanchion_np.node().addSolid(CollisionTube(a[0], a[1], a[2], b[0], b[1], b[2], radius))
                        stanchion_np.node().setFromCollideMask(OBSTACLE_MASK)
            geomnode.removeAllGeoms()

    def begin_look(self):
        self.look = True

    def end_look(self):
        self.look = False
        self.prev_pos = None

    def MouseTask(self, task):
        if self.mouseWatcherNode.hasMouse():
            (x, y) = self.mouseWatcherNode.getMouse()
            if self.prev_pos:
                if self.look or self.active_char.spinning:
                    h_diff = (x - self.prev_pos[0]) * 180
                    p_diff = (y - self.prev_pos[1]) * 90
                    new_h = clamp_deg_sign(self.char_rig.getH() - h_diff)
                    self.char_rig.setH(new_h)
                    self.cam.setP(self.cam.getP() + p_diff)
                    self.active_char.spin(new_h)
            self.prev_pos = (x, y)
        return task.cont

app = FreeBLiTZ()
app.run()
