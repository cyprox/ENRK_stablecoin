import pickle, numpy as np, itertools
def load(n): return pickle.load(open(f'results/{n}.pkl','rb'))
def ms(x): return x.mean(), 1.96*x.std(ddof=1)/np.sqrt(len(x))
def key(c, ks): return tuple(c.get(k) for k in ks)
def paired(a, b, k='area'):
    """mean and CI of (b-a) per run (a = baseline, b = policy)"""
    d = b['m'][k]-a['m'][k]; return ms(d)
