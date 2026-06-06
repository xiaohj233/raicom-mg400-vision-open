from __future__ import annotations
import errno, socket, threading, time
from contextlib import suppress
from .protocol import dec

def err_text(e: BaseException) -> str:
    code=getattr(e,'winerror',None) or getattr(e,'errno',None)
    if code in {10053, errno.ECONNABORTED}: return 'TCP连接被中止/对端可能重启，等待重连'
    if code in {10054, errno.ECONNRESET}: return 'TCP连接被对端关闭，等待重连'
    if isinstance(e, socket.timeout): return 'TCP接收超时'
    return str(e)

def safe_close(s):
    if not s: return
    with suppress(Exception): s.shutdown(socket.SHUT_RDWR)
    with suppress(Exception): s.close()

def send_line(s, text):
    if s is None: raise RuntimeError('socket未连接')
    msg=str(text)
    if not msg.endswith('\n'): msg+='\n'
    try: s.sendall(msg.encode('utf-8'))
    except OSError as e: raise ConnectionError(err_text(e)) from e

def recv_line(s, timeout=None):
    old=s.gettimeout(); s.settimeout(timeout); data=bytearray()
    try:
        while True:
            try: b=s.recv(1)
            except OSError as e: raise ConnectionError(err_text(e)) from e
            if not b: raise ConnectionError('TCP连接已关闭')
            if b==b'\n': break
            data.extend(b)
    finally:
        with suppress(Exception): s.settimeout(old)
    return data.decode('utf-8','replace').strip('\r\n')

def wait_ack(s, expected, timeout=10):
    if isinstance(expected, str): expected={expected.upper()}
    else: expected={str(x).upper() for x in expected}
    t=time.monotonic()+timeout
    while True:
        left=t-time.monotonic()
        if left<=0: raise TimeoutError('等待ACK超时:'+str(expected))
        line=recv_line(s,left)
        m=dec(line)
        if m.head=='ERR': raise RuntimeError('设备返回错误:'+line)
        if m.raw.upper() in expected or m.head in expected: return line

def send_wait(s, command, expected, timeout, log=None):
    send_line(s, command)
    if log: log('=> '+str(command))
    r=wait_ack(s, expected, timeout)
    if log: log('<= '+r)
    return r

class SocketBox:
    def __init__(self, log=print):
        self.items={}; self.lock=threading.Lock(); self.log=log
    def set_logger(self, log): self.log=log
    def set(self, name):
        def save(client):
            with self.lock:
                old=self.items.get(name)
                if old is not client: safe_close(old)
                self.items[name]=client
        return save
    def get(self,name,msg):
        with self.lock: s=self.items.get(name)
        if s is None: raise RuntimeError(msg)
        return s
    def robot(self): return self.get('robot','Lua未连接')
    def vision(self): return self.get('vision','DVS未连接')

def listen_in_thread(port, name, on_client, log, host='0.0.0.0'):
    def run():
        server=None
        while True:
            try:
                if server is None:
                    server=socket.socket(); server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                    server.bind((host,int(port))); server.listen(5)
                    log(f'等待{name}:{port}')
                c,addr=server.accept(); c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                on_client(c); log(f'{name}已连接:{addr[0]}:{addr[1]}')
            except OSError as e:
                log(f'{name}监听异常:'+err_text(e)); safe_close(server); server=None; time.sleep(1)
    th=threading.Thread(target=run,daemon=True); th.start(); return th
