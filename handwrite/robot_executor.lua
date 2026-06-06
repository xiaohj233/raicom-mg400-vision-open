-- MG400 Lua-side executor for the open-source template.
-- Change IP to the Python computer IP before running on a real robot.

IP,PORT,D="192.168.1.120",5001,1
BLOW=2
n=tonumber
err,sock=TCPCreate(false,IP,PORT)
if err~=0 then print("TCPCreate fail") return end
function w(s) TCPWrite(sock,s.."\n",1) end
function split(s) local a={} for v in string.gmatch(s,"[^,]+") do a[#a+1]=v end return a end
function abs_mv(s,ok,er)
  local a=split(s); local x,y,z,r=n(a[2]),n(a[3]),n(a[4]),n(a[5])
  if x and y and z and r then MovJ({coordinate={x,y,z,r},tool=0,user=0},{SpeedJ=20,AccJ=20,SYNC=1}); w(ok)
  elseif s~="" then w("ERR,"..er) end
end
function jog(s)
  local a=split(s); local x,y,z,r=n(a[2]) or 0,n(a[3]) or 0,n(a[4]) or 0,n(a[5]) or 0
  RelMovL({x,y,z,r},{SpeedL=20,AccL=20,SYNC=1}); w("ACK,JOG")
end
function blow(s)
  local a=split(s); local d=n(a[2]) or BLOW; local t=n(a[3]) or 0.35
  DO(d,1); Wait(t*1000); DO(d,0); w("ACK,BLOW")
end
err=TCPStart(sock,0)
if err~=0 then print("TCPStart fail") return end
DO(D,0); DO(BLOW,0); w("ACK,READY")
while true do
  e,s=TCPRead(sock,0,"string")
  if e==0 then
    if type(s)=="table" then s=s.buf end
    s=tostring(s or ""):gsub("%c",""); c=s:sub(1,1)
    if c=="J" then jog(s)
    elseif c=="H" then JointMovJ({joint={0,0,0,0}},{SpeedJ=20,AccJ=20,SYNC=1}); w("ACK,HOME")
    elseif c=="P" then if #split(s)>=5 then abs_mv(s,"READY_PHOTO","PHOTO") else w("READY_PHOTO") end
    elseif c=="S" then DO(D,n(split(s)[2]) or 0); Wait(100); w("ACK,SUCK")
    elseif c=="B" then blow(s)
    elseif c=="E" then DO(D,0); DO(BLOW,0); w("END")
    elseif c=="M" then abs_mv(s,"ACK,MOVE","MOVE")
    elseif c=="Q" then DO(D,0); DO(BLOW,0); w("BYE"); break
    elseif s~="" then w("ERR,UNKNOWN") end
  end
  Wait(10)
end
