
from serialConfig import PortsInfo
from serialObject import SerialConnection

if __name__ == '__main__':

    portData = PortsInfo()
    conn = SerialConnection(portData)

    while True:
        print("[ 0 ] - Port Configuration")
        print("[ 1 ] - Calibrate")
        print("[ 2 ] - Generate dataset")
        print("[ 3 ] - Analyze")
        print("[ x ] - Exit\n")

        entry = input("Select mode: ")

        if entry == '0':
            portData.parameters()

        elif entry == '1':
            conn.auto_calibration(100)

        elif entry == '2':

            name = str(input("Filename: "))
            samples = int(input("Samples: "))

            conn.csv_generator(name, samples)

        elif entry == '3':
            conn.analysis()

        else:
            print("Goodbye . . .")
            break
