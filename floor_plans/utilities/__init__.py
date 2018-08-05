# from itertools import tee, izip

def dict_zip(a, b):
	for k, av in a.items():
		if k in b:
			yield av, b[v]

# def pairwise(iterable):
#     "s -> (s0,s1), (s1,s2), (s2, s3), ..."
#     a, b = tee(iterable)
#     next(b, None)
#     return izip(a, b)

def pairwise(iterator):
	l = list(iterator)
	for i, v in enumerate(l):
		yield v, l[i-1]