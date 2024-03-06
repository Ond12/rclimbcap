from ForceDataContainer import *
from testUI import *
import time

fdc = ForcesDataC(200)

st = time.time()
for i in range(2000000):
    list = [i,i,i,i,i,i]
    fdc.add_data_pointlist(list)
et = time.time()
print(et-st)
print(fdc.num_data_points)
# print(fdc.get_forces_and_moments())

st = time.time()
for i in range(2000000):
    list = [i,i,i,i,i,i]
    fdc.add_data_point(i,i,i,i,i,i)
et = time.time()
print(et-st)
# print(fdc.get_forces_and_moments())

fdc = ForcesData(200)

st = time.time()
for i in range(2000000):
    list = [i,i,i,i,i,i]
    fdc.add_data_point(i,i,i,i,i,i)
et = time.time()
print(et-st)

