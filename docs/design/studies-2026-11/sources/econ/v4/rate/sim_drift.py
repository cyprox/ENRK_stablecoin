from ratelib import *
def run(r0,dt,n,d):
    r=r0
    for _ in range(n): r=step(r,dt,d)
    return r
print("start r0=50,000,000 ppb (5%/yr); total elapsed 1 day; exact after 1 day:")
for d in (-1,1):
    print(' dir',d,'exact',float(exact(50_000_000,86400,d)))
    for dt in (1,10,60,600,3600,86400):
        n=86400//dt
        r=run(50_000_000,dt,n,d)
        print(f'   {n:6d} updates of {dt:5d}s -> r={r:>11d}  ({"allowed" if dt>=DT_MIN else "REJECTED by DT_MIN gate"})')
print("spam: 1 update/s for 30 days, dir=-1 from 5%/yr:")
r=50_000_000
for i in range(30*86400):
    r=step(r,1,-1)
    if r<=RMIN: print('  hits RMIN after',i+1,'s =',(i+1)/86400,'days (exact path would be',float(exact(50_000_000,(i+1),-1)),')'); break
else: print('  r after 30d',r)
print("spam: 1 update/s, dir=+1, from 0.5%/yr, 1 day:", run(RMIN,1,86400,1), 'exact',float(exact(RMIN,86400,1)))
print("gated hourly updates for a year vs exact (dir=-1 from 100%):")
r=RMAX; 
for i in range(24*365): r=step(r,3600,-1)
print('  ->',r,'exact (clamped at RMIN anyway)',float(exact(RMAX,365*86400,-1)))
r=RMAX; 
for i in range(24*30): r=step(r,3600,-1)
print('  30d hourly steps from 1e9 dir=-1:',r,'exact',float(Decimal(RMAX)*Decimal(2)**(Decimal(-30*86400)/H)))
