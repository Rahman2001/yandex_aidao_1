import numpy

data = numpy.load("qualifiers_track_1/data/ts_cut/ihb.npy")
data_dim = numpy.ndim(data)

print(f'\nData dimensions: {data_dim}\n')

for dim in range(data_dim):
    sub_dim = numpy.ndim(data[dim])
    print(f'Dimension: {dim + 1}, sub-dimensions: {sub_dim}')
    if sub_dim > 0:
        for sdim in range(sub_dim):
            sub_sub_dim = numpy.ndim(data[dim][sdim])
            print(f'Sub-dimension: {sdim + 1}, sub-sub-dimension: {sub_sub_dim}')
    print(" ------------------------------------------ ")
