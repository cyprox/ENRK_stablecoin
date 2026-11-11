import random, math
from decimal import Decimal, getcontext
getcontext().prec=60
I64=2**63-1
Q=2**30; LN2_Q=744261118; H=2592000; DT_MIN=3600; DT_MAX=1296000; RMIN=5_000_000; RMAX=1_000_000_000
class Ov(Exception): pass
def tdiv(a,b):
    if b==0: raise ZeroDivisionError
    q=abs(a)//abs(b); return q if (a<0)==(b<0) else -q
def ck(x):
    if x>I64 or x<-I64-1: raise Ov()
    return x
def mul(a,b): return ck(a*b)
def exp_q(x):
    a=ck(Q+tdiv(x,6))
    for k in (5,4,3,2):
        a=ck(Q+tdiv(tdiv(mul(x,a),Q),k))
    return ck(Q+tdiv(mul(x,a),Q))
def step(r,dt,d):
    d1=min(dt,DT_MAX)
    x=tdiv(mul(d1,LN2_Q),H)
    e=exp_q(x)
    nr=r
    if d>0: nr=tdiv(mul(r,e),Q)
    if d<0: nr=tdiv(mul(r,Q),e)
    nr=max(nr,RMIN); nr=min(nr,RMAX)
    return nr
def step_safe(r,dt,d):
    try: return step(r,dt,d)
    except Ov: return 'OVF'
    except ZeroDivisionError: return 'DIV0'
def exact(r,dt,d):
    d1=min(dt,DT_MAX)
    v=Decimal(r)*(Decimal(2)**(Decimal(d)*Decimal(d1)/Decimal(H)))
    return min(max(v,Decimal(RMIN)),Decimal(RMAX))
