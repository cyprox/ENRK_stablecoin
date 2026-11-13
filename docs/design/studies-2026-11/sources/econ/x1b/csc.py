import drv, sc, json
X=drv.X; N=4; tag='ctl4'; v=15_000_000*N; coll=300_000_000; debt=100_000_000
env0=dict(X1B_DIR=X+'/actl/n4', VARIANT='a')
gf=sc.split(tag+'g',1,N*v+30_000_000)[0]
rf=sc.split(tag+'r',6,v+150_000_000)
vf=sc.split(tag+'v',1,coll+30_000_000)[0]
P=lambda k: X+'/out/pop_%s_%d.json'%(tag,k)
g=drv.run('gen_'+tag,'step_genesis',dict(env0,N=N,V=v,PRICE=100_000_000,FUND='%s %d %d'%gf,POP_OUT=P(0)))
assert g.get('status')=='SUBMITTED'; env0['ORACLE_ID']=g['COVENANT_ID']
vg=drv.run('vgen_'+tag,'step_vgen',dict(env0,COLLATERAL=coll,DEBT=debt,FUND='%s %d %d'%vf)); assert vg.get('status')=='SUBMITTED'
vtx=[json.loads(l) for l in open(drv.LEDGER) if json.loads(l)['label']=='vgen_'+tag][-1]['txid']
def lastid(lab): return [json.loads(l) for l in open(drv.LEDGER) if json.loads(l)['label']==lab][-1]['txid']
def partial(k,np,sel='0,1'):
    r=drv.run('refresh_partial_%s_%d'%(tag,k),'step_refresh',dict(env0,POP=P(k-1),POP_OUT=P(k),NEWPRICE=np,PARTIAL=sel,REFRESH_ENTRY='refresh_partial',FUND='%s %d %d'%rf[k-1])); assert r.get('status')=='SUBMITTED'
partial(1,90_000_000)
venv=dict(env0,VAULT_ID=vg['VAULT_ID'],VAULT_TXID=vtx,VAULT_INDEX=0,COLLATERAL=coll,DEBT=debt)
print('LOCAL withdraw 1e8 reading FRESH slot1 (0.90):',drv.build('step_vault',dict(venv,POP=P(1),SLOT=1,ENTRY='withdraw',WITHDRAW=100_000_000)).get('BUILD_FAILED','ACCEPTED?')[:160])
w=drv.run('STALE_withdraw_'+tag,'step_vault',dict(venv,POP=P(1),SLOT=2,ENTRY='withdraw',WITHDRAW=100_000_000))
assert w.get('status')=='SUBMITTED'
wtx=lastid('STALE_withdraw_'+tag)
pop=json.load(open(P(1)))
for e in pop:
    if e['slot']==2: e['txid']=wtx; e['index']=0
json.dump(pop,open(P(1),'w'))
partial(2,81_000_000); partial(3,72_900_000)
venv=dict(venv,VAULT_TXID=wtx,VAULT_INDEX=1,COLLATERAL=coll-100_000_000)
l=drv.run('liquidate_'+tag,'step_vault',dict(venv,POP=P(3),SLOT=1,ENTRY='liquidate'))
assert l.get('status')=='SUBMITTED'
ltx=lastid('liquidate_'+tag)
pop=json.load(open(P(3)))
for e in pop:
    if e['slot']==1: e['txid']=ltx; e['index']=0
json.dump(pop,open(P(3),'w'))
drv.run('drain_lead_s1_'+tag,'step_refresh',dict(env0,POP=P(3),PARTIAL='0,1',NEWPRICE=1,DRAIN=1,FUND='%s %d %d'%rf[3]))
for i,s in ((4,2),(5,3)):
    drv.run('drain_one_s%d_%s'%(s,tag),'step_refresh',dict(env0,POP=P(3),PARTIAL=str(s),NEWPRICE=1,DRAIN=1,DRAIN_ENTRY='drain_one',FUND='%s %d %d'%rf[i]))
