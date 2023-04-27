import numpy as np
import asciichartpy

def print_multiline_plot(x_data_list, y_data_list, width=80, height=20, padding=3):
    min_x = min(min(x_data) for x_data in x_data_list)
    max_x = max(max(x_data) for x_data in x_data_list)
    x_interp = np.linspace(min_x, max_x, width)

    y_interp_list = []
    for x_data, y_data in zip(x_data_list, y_data_list):
        y_interp = np.interp(x_interp, x_data, y_data)
        y_interp_list.append(y_interp.tolist())

    config = {
        'height': height,
        'width': width,
        'padding': padding,
        'colors': [
            asciichartpy.blue,
            asciichartpy.green,
            "s",
            asciichartpy.default,
        ]
    }
    plot = asciichartpy.plot(y_interp_list, config)
    print(plot)


# Example usage with some data
# x_data1 = [1, 3, 5, 6, 7, 10, 12]
# y_data1 = [10, 20, 30, 25, 35, 40, 15]
# x_data2 = [1, 4, 6, 8, 10, 11, 12]
# y_data2 = [5, 15, 20, 22, 30, 25, 10]
# print_multiline_plot([x_data1, x_data2], [y_data1, y_data2])
