"""Strict stdlib vector equivalents for 26885 deterministic numeric regressions.

Prevents a host-only numpy dependency in the successful Actions Python 3.12
workflow. This is a math-fixture helper, NEVER a real language compiler.
"""
import math, builtins
class Array(tuple):
 def __new__(cls,items):return super().__new__(cls,map(float,items))
 def _op(self,o,fn):
  if isinstance(o,(list,tuple)):
   assert len(self)==len(o)
   return Array(fn(a,b) for a,b in zip(self,o))
  return Array(fn(a,o) for a in self)
 def __add__(self,o):return self._op(o,lambda a,b:a+b)
 __radd__=__add__
 def __sub__(self,o):return self._op(o,lambda a,b:a-b)
 def __rsub__(self,o):return Array(o)._op(self,lambda a,b:a-b) if isinstance(o,(list,tuple)) else Array(o-a for a in self)
 def __mul__(self,o):return self._op(o,lambda a,b:a*b)
 __rmul__=__mul__
 def __truediv__(self,o):return self._op(o,lambda a,b:a/b)
 def __rtruediv__(self,o):return Array(o)._op(self,lambda a,b:a/b) if isinstance(o,(list,tuple)) else Array(o/a for a in self)
 def __neg__(self):return Array(-a for a in self)
 def min(self):return builtins.min(self)
 def max(self):return builtins.max(self)
 def copy(self):return Array(self)
def array(x):return Array(x)
def full(n,x):return Array([x]*n)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def clip(x,lo,hi):
 if isinstance(x,(tuple,list)):return Array(builtins.max(lo,builtins.min(hi,a)) for a in x)
 return builtins.max(lo,builtins.min(hi,x))
def maximum(x,y):
 if isinstance(x,(tuple,list)):return Array(builtins.max(a,b) for a,b in zip(x,y)) if isinstance(y,(tuple,list)) else Array(builtins.max(a,y) for a in x)
 return builtins.max(x,y)
def array_equal(a,b):return type(a)==type(b) and all(x==y for x,y in zip(a,b)) and len(a)==len(b)
class _LinAlg:
 @staticmethod
 def norm(x):return math.sqrt(sum(y*y for y in x))
linalg=_LinAlg()
def ones(n):return Array([1.0]*n)
def abs(x):return Array(builtins.abs(v) for v in x) if isinstance(x,(tuple,list)) else builtins.abs(x)
def max(x):return builtins.max(x)
