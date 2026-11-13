import subprocess, os, json, time, re, urllib.request, sys
SP='/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad'
X=SP+'/econ/x1b'
ADDR=open(SP+'/tn10/tn10_address.txt').read().strip()
LEDGER=X+'/ledger.jsonl'
def balance():
    return json.load(urllib.request.urlopen(urllib.request.Request('https://api-tn10.kaspa.org/addresses/%s/balance'%ADDR,headers={'User-Agent':'curl/8'})))['balance']
def curl(url):
    return subprocess.run(['curl','-s',url],capture_output=True,text=True).stdout
def build(test, env):
    e=dict(os.environ); e.update({k:str(v) for k,v in env.items()})
    e.setdefault('X1B_DIR',X+'/b/n4'); e.update(CARGO_TARGET_DIR=SP+'/target', TN10_DIR=SP+'/tn10', X1B_OUT=X+'/out')
    r=subprocess.run(['cargo','test','--offline','--test','x1b',test,'--','--nocapture'],cwd=SP+'/w/argent',env=e,capture_output=True,text=True)
    out=r.stdout+r.stderr
    d={}
    for line in out.splitlines():
        for key in ('TXID','MASS','NEXT_FUND','COVENANT_ID','VAULT_ID','BUILD_FAILED'):
            if line.startswith(key+' '): d[key]=line[len(key)+1:].strip()
    if 'panicked' in out: d['PANIC']=out[out.find('panicked'):][:400]
    return d
def submit(txjson):
    e=dict(os.environ); e['CARGO_TARGET_DIR']=SP+'/target_rpc'
    for t in range(4):
        r=subprocess.run(['cargo','run','-q','--offline','--bin','submit','--',txjson],cwd=SP+'/rpc',env=e,capture_output=True,text=True)
        o=(r.stdout+r.stderr)
        m=re.search(r'^(SUBMITTED|REJECTED) (.*)$',o,re.M)
        if m: return m.group(1),m.group(2)
        time.sleep(3)
    return 'ERROR',o[-300:]
def wait(txid,t0,maxs=60):
    for i in range(maxs):
        b=curl('https://api-tn10.kaspa.org/transactions/%s?inputs=false&outputs=false'%txid)
        try:
            j=json.loads(b)
            if j.get('is_accepted'):
                return j.get('mass'), round(time.time()-t0,1)
        except Exception: pass
        time.sleep(1)
    return None,None
def run(label, test, env, submit_it=True, expect_reject=False):
    """build, submit, wait; ledger line. Returns dict (incl. NEXT_FUND parts)."""
    d=build(test,env)
    if 'BUILD_FAILED' in d or 'PANIC' in d or 'TXID' not in d:
        print('[%s] BUILD_FAILED %s'%(label,d.get('BUILD_FAILED',d.get('PANIC','?'))[:400])); return d
    txf=X+'/out/tx_%s.json'%({'step_genesis':'genesis','step_vgen':'vgen','step_split':'split','step_use_only':'use_only'}.get(test) or (('drain' if env.get('DRAIN') else 'refresh') if test=='step_refresh' else 'vault_'+env.get('ENTRY','')))
    keep=X+'/out/%s.json'%label; subprocess.run(['cp',txf,keep])
    if not submit_it:
        print('[%s] BUILT %s mass %s'%(label,d['TXID'],d.get('MASS'))); return d
    t0=time.time()
    st,msg=submit(keep)
    rec=dict(label=label,txid=d['TXID'],local_mass=d.get('MASS'),submit=st,msg=msg[:600])
    if st=='SUBMITTED':
        am,secs=wait(d['TXID'],t0)
        rec.update(api_mass=am,confirm_s=secs)
    rec['balance_after']=balance() if st=='SUBMITTED' else None
    open(LEDGER,'a').write(json.dumps(rec)+'\n')
    print('[%s] %s %s | local %s | api_mass %s | %ss | %s'%(label,st,d['TXID'][:16] if st=='SUBMITTED' else '',d.get('MASS'),rec.get('api_mass'),rec.get('confirm_s'),msg[:300] if st!='SUBMITTED' else ''))
    d['status']=st
    return d
