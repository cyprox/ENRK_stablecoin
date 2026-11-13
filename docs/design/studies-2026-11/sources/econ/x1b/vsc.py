import drv, sc, sys, json
X=drv.X
var=sys.argv[1]; N=int(sys.argv[2]); vdir=sys.argv[3]; tag='v'+var+str(N)
v=15_000_000*N; coll=160_000_000; debt=100_000_000
env0=dict(X1B_DIR=X+'/%s/n%d'%(vdir,N), VARIANT=var[0])
gf=sc.split(tag+'g',1,N*v+30_000_000)[0]
rf=sc.split(tag+'r',7,v+150_000_000)
vf=sc.split(tag+'v',1,coll+30_000_000)[0]
P=lambda k: X+'/out/pop_%s_%d.json'%(tag,k)
g=drv.run('gen_'+tag,'step_genesis',dict(env0,N=N,V=v,PRICE=100_000_000,FUND='%s %d %d'%gf,POP_OUT=P(0)))
assert g.get('status')=='SUBMITTED'
env0['ORACLE_ID']=g['COVENANT_ID']
vg=drv.run('vgen_'+tag,'step_vgen',dict(env0,COLLATERAL=coll,DEBT=debt,FUND='%s %d %d'%vf))
assert vg.get('status')=='SUBMITTED'
vid=vg['VAULT_ID']; vtx=vg['TXID']
# need vault txid: from ledger
vtx=[json.loads(l) for l in open(drv.LEDGER) if json.loads(l)['label']=='vgen_'+tag][-1]['txid']
venv=dict(env0,VAULT_ID=vid,VAULT_TXID=vtx,COLLATERAL=coll,DEBT=debt,ENTRY='liquidate',SLOT=1)
rounds=[90_000_000,99_000_000,89_100_000]
for k,np in enumerate(rounds):
    r=drv.run('refresh_%s_%d'%(tag,k+1),'step_refresh',dict(env0,POP=P(k),POP_OUT=P(k+1),NEWPRICE=np,FUND='%s %d %d'%rf[k]))
    assert r.get('status')=='SUBMITTED'
    if k==1:
        # price 0.99 (ICR 158.4): not liquidatable -> build must refuse (LOCAL)
        print('LOCAL not-liquidatable @0.99:',drv.build('step_vault',dict(venv,POP=P(2),X1B_OUT=X+'/out')).get('BUILD_FAILED','ACCEPTED?')[:200])
        # attack 1: liquidate with OLD sibling of round 1 (price 0.90, spent outpoint) -> node must refuse
        drv.run('ATTACK_liq_old_sibling_'+tag,'step_vault',dict(venv,POP=P(1)))
        # attack 2: plain `use` of an old (spent) sibling
        drv.run('ATTACK_use_old_sibling_'+tag,'step_use_only',dict(env0,POP=P(0),SLOT=1,FUND='%s %d %d'%rf[5]))
# now pop_3 at 0.891 (ICR 142.6): legit liquidation reading the new price
l=drv.run('liquidate_new_price_'+tag,'step_vault',dict(venv,POP=P(3)))
# attack 3 after liquidation: old sibling again (round 2 pop, spent)
drv.run('ATTACK_use_old_sibling2_'+tag,'step_use_only',dict(env0,POP=P(2),SLOT=3,FUND='%s %d %d'%rf[6]))
# drain
cur=P(3)
# the liquidation recreated slot-1 price utxo: update pop_3 entry for slot 1
txid=[json.loads(x) for x in open(drv.LEDGER) if json.loads(x)['label']=='liquidate_new_price_'+tag][-1]['txid']
pop=json.load(open(cur))
for e in pop:
    if e['slot']==1: e['txid']=txid; e['index']=0 if False else 0
json.dump(pop,open(P(4),'w'))
drv.run('drain_'+tag,'step_refresh',dict(env0,POP=P(4),NEWPRICE=1,DRAIN=1,FUND='%s %d %d'%rf[3]))
