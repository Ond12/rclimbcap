import pandas as pd

class AnalogData:
    def __init__(self, frequency, num_channels):
        self.frequency = frequency
        self.num_data_points = 0
        self.num_channels = num_channels
        self.capacity = 12000
        self.write_index = 0
        
        self.datas = [[0] * self.capacity for _ in range(self.num_channels)]
        
        self.x_time = [0] * self.capacity
        
    def write_or_append_data(self, array, index, value):
        if index < self.capacity:
            array[index] = value
        else:
            array.append(value)

    def add_data_point(self, analog_data):

        self.num_data_points += 1
        self.write_index += 1
        
        for i, sub_list in enumerate(self.datas):
            self.write_or_append_data(sub_list, self.write_index, analog_data[i])

        # time_val = (1 / self.frequency) * self.write_index
        # self.write_or_append_data(self.x_time, self.write_index, time_val)

    def to_dataframe(self):
        data_dict = {
            f'analog_{i+1}': data[0:self.num_data_points] for i, data in enumerate(self.datas)
        }
        df = pd.DataFrame(data_dict)
        return df
