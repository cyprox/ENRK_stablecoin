import json, collections, re
exec(open('gen_icr.py').read().split("cases=[]")[0])  # reuse helpers (reseeds, harmless)
meta=json.load(open('meta_icr.json')); out=open('out_icr.txt').read().splitlines()
stat=collections.Counter(); bad=[]
for m,o in zip(meta,out):
    entry,c,p,d,r,tag=m; acc=o.split()[1]=='ACCEPT'; msg=o[o.find('REJECT')+7:] if not acc else ''
    if entry=='unguarded':
        pred=unguarded(c,p,d)
        if pred in('OVF','DIV0'):
            exp='REJ-'+pred
            got='ACC' if acc else ('REJ-OVF' if 'too big' in msg else 'REJ-DIV0' if 'ivi' in msg and 'zero' in msg.lower() else 'REJ-OTHER')
        else:
            exp='ACC' if pred==r else 'REJ-OTHER'   # pred==ref when no overflow & positive
            got='ACC' if acc else ('REJ-OVF' if 'too big' in msg else 'REJ-OTHER')
        stat[(entry,tag,exp==got or (exp.startswith('REJ') and got.startswith('REJ') and pred in('OVF','DIV0')))]+=1
        stat[(entry,'ALL','outcome:'+got)]+=1
        if not (exp==got or (exp.startswith('REJ') and got.startswith('REJ'))): bad.append((m,o,pred))
        # classification of exact-correctness: when ACC, must equal ref
    else:
        if inb(c,p,d): exp='ACC'
        else: exp='REJ'
        got='ACC' if acc else 'REJ'
        stat[(entry,tag,exp==got)]+=1; stat[(entry,'ALL','outcome:'+got+(' inb' if inb(c,p,d) else ' oob'))]+=1
        if exp!=got: bad.append((m,o,None))
for k in sorted(stat,key=str): print(k,stat[k])
print('MISMATCHES',len(bad)); print(bad[:6])
# distinct engine messages
msgs=collections.Counter(re.sub(r'\d+','N',o.split(None,2)[2]) for o in out if 'REJECT' in o)
print(msgs.most_common(6))
