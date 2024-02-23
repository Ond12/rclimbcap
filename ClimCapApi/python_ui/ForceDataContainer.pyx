# Importing necessary Cython and C types
import numpy as np
from libc.stdlib cimport malloc, free, realloc

# Declare the ForcesDataC class
cdef class ForcesDataC:
    cdef double* forces_x
    cdef double* forces_y
    cdef double* forces_z
    cdef double* moments_x
    cdef double* moments_y
    cdef double* moments_z

    cdef public int num_data_points
    cdef int capacity
    cdef public double frequency

    # Constructor to initialize the class
    def __cinit__(self, double frequency):
        self.frequency = frequency
        self.num_data_points = 0
        self.capacity = 20000
        self.allocate_memory()

    # Method to allocate memory for the arrays
    cdef allocate_memory(self):
        self.forces_x  = <double*>malloc(self.capacity * sizeof(double))
        self.forces_y  = <double*>malloc(self.capacity * sizeof(double))
        self.forces_z  = <double*>malloc(self.capacity * sizeof(double))
        self.moments_x = <double*>malloc(self.capacity * sizeof(double))
        self.moments_y = <double*>malloc(self.capacity * sizeof(double))
        self.moments_z = <double*>malloc(self.capacity * sizeof(double))

        # Method to add a new data point
    cpdef add_data_pointlist(self, list force_vals):
        if self.num_data_points >= self.capacity:
            self.capacity *= 2
            self.reallocate_memory()

        self.forces_x[self.num_data_points]  = force_vals[0]
        self.forces_y[self.num_data_points]  = force_vals[1]
        self.forces_z[self.num_data_points]  = force_vals[2]
        self.moments_x[self.num_data_points] = force_vals[3]
        self.moments_y[self.num_data_points] = force_vals[4]
        self.moments_z[self.num_data_points] = force_vals[5]

        self.num_data_points += 1

    # Method to add a new data point
    cpdef add_data_point(self, double force_x_val, double force_y_val, double force_z_val, double moment_x_val, double moment_y_val, double moment_z_val):
        if self.num_data_points >= self.capacity:
            self.capacity *= 2
            self.reallocate_memory()

        self.forces_x[self.num_data_points] = force_x_val
        self.forces_y[self.num_data_points] = force_y_val
        self.forces_z[self.num_data_points] = force_z_val
        self.moments_x[self.num_data_points] = moment_x_val
        self.moments_y[self.num_data_points] = moment_y_val
        self.moments_z[self.num_data_points] = moment_z_val

        self.num_data_points += 1

    # Method to reallocate memory when needed
    cdef reallocate_memory(self):
        self.forces_x  = <double*>realloc(self.forces_x,  self.capacity  * sizeof(double))
        self.forces_y  = <double*>realloc(self.forces_y,  self.capacity  * sizeof(double))
        self.forces_z  = <double*>realloc(self.forces_z,  self.capacity  * sizeof(double))
        self.moments_x = <double*>realloc(self.moments_x, self.capacity  * sizeof(double))
        self.moments_y = <double*>realloc(self.moments_y, self.capacity  * sizeof(double))
        self.moments_z = <double*>realloc(self.moments_z, self.capacity  * sizeof(double))

    cpdef tuple get_forces_and_moments(self):
        # Convert C arrays to Python lists
        forces_x_list =  [self.forces_x[i]  for i in range(self.num_data_points)]
        forces_y_list =  [self.forces_y[i]  for i in range(self.num_data_points)]
        forces_z_list =  [self.forces_z[i]  for i in range(self.num_data_points)]
        moments_x_list = [self.moments_x[i] for i in range(self.num_data_points)]
        moments_y_list = [self.moments_y[i] for i in range(self.num_data_points)]
        moments_z_list = [self.moments_z[i] for i in range(self.num_data_points)]

        forces = (forces_x_list, forces_y_list, forces_z_list)
        moments = (moments_x_list, moments_y_list, moments_z_list)
        return forces, moments

    cpdef list get_forces_x(self):
        forces_x_list =  [self.forces_x[i]  for i in range(self.num_data_points)]
        return forces_x_list

    cpdef list get_forces_y(self):
        forces_y_list =  [self.forces_y[i]  for i in range(self.num_data_points)]
        return forces_y_list
    
    cpdef list get_forces_z(self):
        forces_z_list =  [self.forces_z[i]  for i in range(self.num_data_points)]
        return forces_z_list

    cpdef set_force_x(self, data):
        num_elements = len(data)
        if num_elements > self.capacity:
            self.capacity = num_elements
            self.reallocate_memory()
        self.num_data_points = num_elements
        for i in range(self.num_data_points):
            self.forces_x[i] = data[i]

    # Method to set forces_y values
    cpdef set_force_y(self, data):
        num_elements = len(data)
        if num_elements > self.capacity:
            self.capacity = num_elements
            self.reallocate_memory()
        self.num_data_points = num_elements
        for i in range(self.num_data_points):
            self.forces_y[i] = data[i]

    # Method to set forces_z values
    cpdef set_force_z(self, data):
        num_elements = len(data)
        if num_elements > self.capacity:
            self.capacity = num_elements
            self.reallocate_memory()
        self.num_data_points = num_elements
        for i in range(self.num_data_points):
            self.forces_z[i] = data[i]
    
    def __dealloc__(self):
        free(self.forces_x)
        free(self.forces_y)
        free(self.forces_z)
        free(self.moments_x)
        free(self.moments_y)
        free(self.moments_z)
