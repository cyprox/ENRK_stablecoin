import json,math,sys
R='/private/tmp/claude-501/-Users-simoes-ENRK-stablecoin/2186f877-edaf-4d28-afb8-7195b5d7c758/scratchpad/raw/'
def L(f):return json.load(open(R+f))
def bids(n):
  d=L('ob_%s.json'%n)
  if n=='kraken':b=d['result']['KASUSD']['bids']
  elif n=='kucoin':b=d['data']['bids']
  elif n=='bybit':b=d['result']['b']
  elif n=='bitget':b=d['data']['bids']
  else:b=d['bids']
  return [(float(x[0]),float(x[1])) for x in b]
vol={}
vol['kraken']=float(L('t_kraken.json')['result']['KASUSD']['v'][1])
vol['kucoin']=float(L('t_kucoin.json')['data']['volValue'])/float(L('t_kucoin.json')['data']['last'])
vol['mexc']=float(L('t_mexc.json')['volume'])
vol['gate']=float(L('t_gate.json')[0]['base_volume'])
vol['bybit']=float(L('t_bybit.json')['result']['list'][0]['volume24h'])
vol['bitget']=None
tot=0
for n in['kraken','kucoin','gate','mexc','bybit','bitget']:
  b=sorted(bids(n),reverse=True);mid=b[0][0]
  depth=sum(q for p,q in b);lo=b[-1][0]
  print(n,'best bid',mid,'levels',len(b),'lowest px',lo,'(%.1f%% below)'%(100*(1-lo/mid)),'bid KAS',round(depth),'24h KAS vol',vol[n])
  for pct in(1,2,5):
    lim=mid*(1-pct/100);print('   bid depth within %d%%: %.0f KAS (%.0f USD)'%(pct,sum(q for p,q in b if p>=lim),sum(q*p for p,q in b if p>=lim)))
  adv=vol[n]
  if adv:
    for f in(.001,.01,.05):
      Q=f*adv;rem=Q;got=0
      for p,q in b:
        t=min(rem,q);got+=t*p;rem-=t
        if rem<=0:break
      if rem>0:print('   sell %.1f%% ADV=%.0f KAS: EXCEEDS visible book (unfilled %.0f)'%(f*100,Q,rem));continue
      sl=1-(got/Q)/mid;k=sl/math.sqrt(f);print('   sell %.1f%% ADV=%.0f KAS: avg slippage %.3f%% k=%.3f; marginal px %.3f%%'%(f*100,Q,sl*100,k,100*(1-p/mid)))
