import drv, json, sys, os
X=drv.X
def bank(): 
    p=open(X+'/bank.txt').read().split(); return ' '.join(p)
def setbank(s): open(X+'/bank.txt','w').write(s)
if not os.path.exists(X+'/bank.txt'): setbank(open(X+'/bank0.txt').read().strip())

def split(tag, k, v):
    r=drv.run('split_'+tag,'step_split',dict(FUND=bank(),K=k,V=v))
    if r.get('status')!='SUBMITTED': raise SystemExit('split failed')
    t,idx,amt=r['NEXT_FUND'].split(); setbank(r['NEXT_FUND'])
    return [(t,i,v) for i in range(k)]

def scenario(var, N, vdir, rounds, price0=100_000_000, vmult=15_000_000, tag=None, dodrain=True, vault=None, gf=None, rf=None):
    tag=tag or '%s%d'%(var,N)
    v=vmult*N
    env0=dict(X1B_DIR=X+'/%s/n%d'%(vdir,N), VARIANT=var[0])
    gf=gf or split(tag+'g',1,N*v+30_000_000)[0]
    rf=rf or split(tag+'r',len(rounds)+2,v+150_000_000)
    pop=X+'/out/pop_%s_0.json'%tag
    g=drv.run('gen_'+tag,'step_genesis',dict(env0,N=N,V=v,PRICE=price0,FUND='%s %d %d'%gf,POP_OUT=pop))
    if g.get('status')!='SUBMITTED': return g
    oid=g['COVENANT_ID']; env0['ORACLE_ID']=oid
    res=[g]; cur=pop
    for k,(np,) in enumerate([(r,) for r in rounds]):
        nxt=X+'/out/pop_%s_%d.json'%(tag,k+1)
        r=drv.run('refresh_%s_%d'%(tag,k+1),'step_refresh',dict(env0,POP=cur,POP_OUT=nxt,NEWPRICE=np,FUND='%s %d %d'%rf[k]))
        res.append(r)
        if r.get('status')!='SUBMITTED': break
        cur=nxt
    if dodrain:
        r=drv.run('drain_'+tag,'step_refresh',dict(env0,POP=cur,NEWPRICE=1,DRAIN=1,FUND='%s %d %d'%rf[len(rounds)]))
        res.append(r)
    return res
if __name__=='__main__':
    var,N=sys.argv[1],int(sys.argv[2]); vdir=sys.argv[3]
    rounds=[int(x) for x in sys.argv[4].split(',')]
    print(scenario(var,N,vdir,rounds))
