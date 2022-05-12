import serial.tools.list_ports


class PortsInfo:
    def __init__(self):
        self.__ports = serial.tools.list_ports.comports()
        self.port = "/dev/ttyUSB0"
        #self.port = "COM12"
        self.speed = 115200

    def show_ports(self):
        for port, desc, hwd in sorted(self.__ports):
            print("{}: {}".format(port, desc))

    def parameters(self):
        self.show_ports()

        self.port = input("PORT Label: ")
        self.speed = input("Baud Rate: ")

        print(f'PORT: {self.port}')
        print(f'Baud Rate: {self.speed}')
