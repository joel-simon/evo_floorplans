import random
# from numpy.random import choice

def weighted_choice(choices):
   total = sum(w for w,c in choices)
   r = random.uniform(0, total)
   upto = 0
   for w, c in choices:
      if upto + w >= r:
         return c
      upto += w
   assert False, "Shouldn't get here"


# def weighted_choice(choices):
#     return choice(*zip(choices))
