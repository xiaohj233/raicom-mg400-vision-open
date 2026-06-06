from __future__ import annotations
import time
from .protocol import move_cmd, suck_cmd, blow_cmd, photo_cmd, home_cmd, jog_cmd, end_cmd
from .transport import send_line, wait_ack

class RobotJogger:
    def __init__(self,socket_getter,log,step=10): self.get=socket_getter; self.log=log; self.step=step
    def send(self,c):
        try: send_line(self.get(),c); self.log('=> '+c)
        except Exception as e: self.log('错误:'+str(e))
    def jog(self,dx=0,dy=0,dz=0,dr=0): self.send(jog_cmd(dx,dy,dz,dr))
    def home(self): self.send(home_cmd())

def move_wait(s,x,y,z,r,timeout,log):
    send_line(s, move_cmd(x,y,z,r)); rpl=wait_ack(s,('ACK,MOVE',),timeout); log('ROBOT '+rpl); return rpl

def suck_wait(s,on,timeout,log):
    send_line(s, suck_cmd(on)); rpl=wait_ack(s,('ACK,SUCK',),timeout); log('ROBOT '+rpl); return rpl

def blow_wait(s,do,seconds,timeout,log):
    send_line(s, blow_cmd(do,seconds)); rpl=wait_ack(s,('ACK,BLOW','ACK,SUCK'),timeout); log('ROBOT '+rpl); return rpl

def release_wait(s,cfg,timeout,log):
    for i in range(cfg.release_retry):
        suck_wait(s,0,timeout,log)
        if cfg.release_blow_s>0: blow_wait(s,cfg.release_do,cfg.release_blow_s,timeout,log)
        if cfg.release_wait_s>0: log(f'RELEASE wait {cfg.release_wait_s:.2f}s ({i+1}/{cfg.release_retry})'); time.sleep(cfg.release_wait_s)

def photo_wait(s,pose,timeout,log):
    c=photo_cmd(pose); send_line(s,c); log('=> '+c); r=wait_ack(s,('READY_PHOTO',),timeout); log('<= '+r); return r

def execute_pick_place(s,t,place,cfg,timeout,log):
    pa=cfg.pick_z+abs(cfg.pick_delta)
    px=t.robot_x+getattr(cfg,'pick_dx',0.0)
    py=t.robot_y+getattr(cfg,'pick_dy',0.0)
    if getattr(cfg,'pick_dx',0.0) or getattr(cfg,'pick_dy',0.0):
        log(f'PICK_OFFSET dx={cfg.pick_dx:.2f} dy={cfg.pick_dy:.2f} -> ({px:.2f},{py:.2f})')
    move_wait(s,px,py,cfg.safe_z,t.angle,timeout,log)
    move_wait(s,px,py,pa,t.angle,timeout,log)
    move_wait(s,px,py,cfg.pick_z,t.angle,timeout,log)
    suck_wait(s,1,timeout,log)
    move_wait(s,px,py,cfg.safe_z,t.angle,timeout,log)
    x,y,z,r=place.as_tuple()
    if place.air_drop:
        log(f'AIR_DROP {place.label} -> ({x:.1f},{y:.1f},{z:.1f},{r:.1f})')
        move_wait(s,x,y,z,r,timeout,log); release_wait(s,cfg,timeout,log); return
    move_wait(s,x,y,cfg.safe_z,r,timeout,log)
    move_wait(s,x,y,z+abs(cfg.place_delta),r,timeout,log)
    move_wait(s,x,y,z,r,timeout,log)
    release_wait(s,cfg,timeout,log)
    move_wait(s,x,y,cfg.safe_z,r,timeout,log)

def end_wait(s,timeout,log):
    send_line(s,end_cmd()); r=wait_ack(s,('END',),timeout); log('ROBOT '+r); return r
