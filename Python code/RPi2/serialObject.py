import serial
import pandas as pd
import time
import numpy as np
from joblib import load


class SerialConnection:
    # Constructor. Sets the port configuration, connection variable and bias variable for calibration.
    def __init__(self, port_data):
        self.__port_data = port_data
        self.__connection = serial.Serial(timeout=1)
        self.__bias = np.array([-130, -85, 935])
        self.__window_size = 100
        self.__window_step = 30
        self.__rules = [0, 0, 0, 0, 0, 0]

    # Starts the SERIAL connection with the given configuration.
    def __start_port(self):
        self.__close_conn()

        self.__connection.port = self.__port_data.port
        self.__connection.baudrate = self.__port_data.speed

        self.__connection.open()

    # Closes the SERIAL connection.
    def __close_conn(self):
        self.__connection.close()

    # Flushes the SERIAL Buffer and reads a line to throw possible incomplete data.
    def __flush_serial(self):
        self.__connection.flushInput()
        self.__connection.readline()

    # Setting the new port configuration (PUBLIC).
    def port_config(self, new_data):
        self.__port_data = new_data
        print(f'{self.__port_data}\n')

    # Sets the bias variable calibration when the accelerometer is not online.
    def auto_calibration(self, samples_calibration):
        print('Calibrating ...')

        # Array to append the information from the accelerometer.
        readings = np.array([0, 0, 0])

        self.__close_conn()
        self.__start_port()
        self.__flush_serial()

        try:
                # Reading 100 samples for calibration.
                for sample in range(0, samples_calibration):

                    # While loop in case there is incomplete information when reading.
                    while True:
                        data = self.__connection.readline()
                        data_decoded = data[0:len(data) - 2].decode("utf-8").split(",")

                        # Validation of the length of the data.
                        if len(data_decoded) == 3:
                            readings = readings + [float(data_decoded[0]), float(data_decoded[1]), float(data_decoded[2])]
                            break

                        else:
                            None
                            # print("Invalid length")

                # Calculating the bias with the readings and the amount of these samples.
                self.__bias = readings / samples_calibration
                print('Done calibrating')
        except:
                print("Couldn't calibrate")

        
        print(f'{self.__bias}\n')
        self.__close_conn()

    # Creates the CSV File for the dataset of samples with the given parameters.
    def csv_generator(self, filename, samples):
        print(f'\n{self.__bias}\n')
        print("Reading...")

        self.__close_conn()
        self.__start_port()
        self.__flush_serial()

        # Creates the time variables for the timestamps.
        out_time = time.time()
        initial_time = out_time
        stamp = 0

        # Empty lists to gather the information.
        timestamps = []
        dataset_x = []
        dataset_y = []
        dataset_z = []

        # Gathers the amount of samples that were specified.
        for sample in range(0, samples):
                while True:
                        try:
                                data = self.__connection.readline()
                                # print(data)
                                data_decoded = data[0:len(data) - 2].decode("utf-8").split(",")
                                if len(data_decoded) == 3:
                                        break
                                print("invalid")
                        except:
                                print("Serial write read")
                                continue

                # Calculates inner time.
                in_time = time.time()

                # Appending the data to the corresponding lists.
                timestamps.append(stamp)
                dataset_x.append(float(data_decoded[0]))
                dataset_y.append(float(data_decoded[1]))
                dataset_z.append(float(data_decoded[2]))

                # Calculates the time difference and update the variables.
                stamp = stamp + (in_time - out_time) * 1000
                out_time = in_time

        # Closes the file.
        dataset = pd.DataFrame({'timestamp': timestamps, 'x': dataset_x, 'y': dataset_y, 'z': dataset_z})
        print("Done reading.")
        print("Processing...")

        # Creates a file with the stats of the collected data (Elapsed time and bias).
        f_stats = open(f"{filename}_stats.txt", "w")
        f_stats.write(f'Elapsed time: {(out_time - initial_time) * 1000} ms \n')
        f_stats.write(f'Bias: {list(self.__bias)} \n')
        f_stats.close()

        # Updating the information with the given calibration. Saving to a CSV file.
        dataset.loc[:, ['x', 'y', 'z']] = dataset.loc[:, ['x', 'y', 'z']] - self.__bias
        dataset.to_csv(f'{filename}.csv', index=False)
        print("Done, file generated.\n")
        self.__close_conn()

    # Shortens the window size.
    def __delete_window(self, window):
        window = np.delete(window, range(0, self.__window_step), 0)
        return window

    # Constantly analyses the information searching for anomalies until the program is interrupted.
    def analysis(self):

        # States for signal sending.
        state_code = ['ATPP', 'ATPP','ATFA', 'ATFB']
        state_label = ['NORMAL', 'NORMAL','FALLA 1', 'FALLA 2']
        count = 0
        curr_state = 0
        prev_state = 10

        self.__close_conn()
        self.__start_port()
        self.__flush_serial()

        window_x = np.array([])
        window_y = np.array([])
        window_z = np.array([])

        # Loading the configuration for the ML model.
        model = load('modelo.joblib')

        # Try/Except to stop at interruption (Ctrl + C)
        try:
            # Continuously reads until the correct data size is read.
            while True:
                data = self.__connection.readline()
                data_decoded = data[0:len(data) - 2].decode("utf-8").split(",")

                out_time = time.time()

                # Length validation.
                if len(data_decoded) == 3:
                    # Gathering the X and Z values.
                    try:
                        data_x = float(data_decoded[0]) - self.__bias[0]
                        data_y = float(data_decoded[1]) - self.__bias[1]
                        data_z = float(data_decoded[2]) - self.__bias[2]    
                    except:
                        # print('Serial read')
                        continue
                    

                    # Appending the values and calculating the RMS for the windows.
                    window_x = np.append(window_x, data_x)
                    window_y = np.append(window_y, data_y)
                    window_z = np.append(window_z, data_z)

                    # Once the size of the array has moved the specified "step".
                    # The first "step" is always missed.
                    if len(window_y) == (self.__window_size + self.__window_step):

                        # Shortening the windows.
                        window_x = self.__delete_window(window_x)
                        window_y = self.__delete_window(window_y)
                        window_z = self.__delete_window(window_z)

                        # Variables being calculated.
                        # -----------------------------------------------
                        rms_x = self.__rms_calculator(window_x)
                        rms_y = self.__rms_calculator(window_y)
                        rms_z = self.__rms_calculator(window_z)

                        std_x = np.std(window_x)
                        std_y = np.std(window_y)
                        std_z = np.std(window_z)

                        max_x = max(np.absolute(window_x))
                        max_y = max(np.absolute(window_y))
                        max_z = max(np.absolute(window_z))

                        # -----------------------------------------------

                        observables = {
                            'max_x': max_x,
                            'std_x': std_x,
                            'rms_x': rms_x,
                            'max_y': max_y,
                            'std_y': std_y,
                            'rms_y': rms_y,
                            'max_z': max_z,
                            'std_z': std_z,
                            'rms_z': rms_z,
                        }

                        data = pd.DataFrame(observables, index=[0])

                        predict = model.predict(data)
                        curr_state = predict[0]

                        in_time = time.time()
                        stamp = (in_time - out_time) * 1000

                        # '''
                        print("# ------------------------")
                        print(f'MAX_X: {max_x}\nMAX_Y: {max_y}\nMAX_Z: {max_z}')
                        print(f'STD_X: {std_x}\nSTD_Y: {std_y}\nSTD_Z: {std_z}')
                        print(f'RMS_X: {rms_x}\nRMS_Y: {rms_y}\nRMS_Z: {rms_z}')
                        # '''

                        print(f'Calculation time: {stamp}')
                        print(f'BUFFER IN : {self.__connection.in_waiting}')
                        print(f'Predict: {curr_state}')
                        print("# ------------------------")

                        # ATFA : Nivel 1
                        # ATFB : Nivel 2
                        # ATPP : Normal

                        # Determinate new state.
                        if curr_state != prev_state:
                                
                                if curr_state == 0 or curr_state == 1:
                                        prev_state = curr_state
                                        count = 0

                                elif curr_state == 2:
                                        prev_state = curr_state
                                        count = 0

                                elif curr_state == 3:
                                        prev_state = curr_state
                                        count = 0
                        
                        # The same state is maintained. 
                        else:
                                count = count + 1
                                
                                # Confirmations reached. 
                                if count == 5:
                                        self.__connection.write(state_code[curr_state].encode())
                                        print(f'# # # # {state_label[curr_state]} # # # #')

                else:
                    None
                    # print("INSUFFICIENT SIZE")

        except KeyboardInterrupt:
            print("Exiting . . .")
            pass

        self.__close_conn()

    # Calculates the RMS values.
    @staticmethod
    def __rms_calculator(window):
        # Calculating rms for the array.
        rms = np.sqrt(np.mean(np.power(window, 2)))
        return rms
