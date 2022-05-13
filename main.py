from tkinter import *
import time
from math import sin, pi
import RPi.GPIO as GPIO


GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)

pins = [17, 27, 22, 23, 24, 25, 16, 26]
pins = pins[::-1]
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)


class Plot:
    margin = 40
    width = 800
    height = 500
    u_max = t_max = None

    def __init__(self):
        self.root = Tk()
        self.root.geometry(str(self.width) + 'x' + str(self.height))
        self.root.title("Plot-huyot")
        self.canvas = Canvas(self.root, width=self.width, height=self.height)
        self.canvas.pack()
        self.create_axes()

    def create_axes(self):
        self.canvas.delete('axes')
        self.canvas.create_line(self.margin, self.height / 2,
                                self.width - self.margin, self.height / 2, arrow=LAST, width=2, tag='axes')
        self.canvas.create_line(self.margin, self.height - self.margin,
                                self.margin, self.margin, arrow=LAST, width=2, tag='axes')
        self.canvas.create_text(self.margin, self.margin / 2, text='U, мB', tag='axes')
        self.canvas.create_text(self.width - self.margin / 2, self.height / 2, text='t, мc', tag='axes')

    def update_grid(self, frequency, amplitude):
        self.canvas.delete('grid')
        delta_t = (1 / frequency) / 2
        for i, _x in enumerate(range(self.margin * 1000,
                                     (self.width-self.margin) * 1000,
                                     round((delta_t * (self.width-2*self.margin)/self.t_max)*1000))):
            x = _x/1000
            self.canvas.create_line(x, self.margin, x, self.height-self.margin, fill='#CCC', tag='grid')
            self.canvas.create_text(x, self.height/2+10, text=str(round(i*delta_t*1000)), tag='grid')

        delta_u = (self.u_max // 100 + 1) * 10
        for i, _y in enumerate(range(self.height * 1000 // 2,
                                     (self.height-self.margin) * 1000,
                                     round(delta_u * (self.height-2*self.margin)/self.u_max * 1000 / 2))):
            y = _y/1000
            self.canvas.create_line(self.margin, y, self.width-self.margin, y, fill='#CCC', tag='grid')
            self.canvas.create_text(self.margin-15, y, text=str(round(-i*delta_u)), tag='grid')
            self.canvas.create_line(self.margin, self.height-y, self.width - self.margin, self.height-y, fill='#CCC', tag='grid')
            self.canvas.create_text(self.margin-15, self.height-y, text=str(round(i * delta_u)), tag='grid')
        self.create_axes()
        self.canvas.update()

    def update_plot(self, frequency, amplitude):
        self.canvas.delete('plot')
        u_max_new = (amplitude//30 + 1) * 30
        t_max_new = 1 / (frequency//10 + 1)
        if u_max_new != self.u_max or t_max_new != self.t_max:
            self.u_max = u_max_new
            self.t_max = t_max_new
            self.update_grid(frequency, amplitude)

        last_x = self.margin
        last_y = self.height/2
        for i in range(0, 1000):
            t = i / 1000 * self.t_max
            x = self.margin + ((self.width - 2 * self.margin) / self.t_max) * t
            y = self.height / 2 + ((self.height / 2 - self.margin) / self.u_max) * \
                (amplitude * sin(2 * pi * frequency * t))
            # self.canvas.create_oval(x, self.height-y, x, self.height-y, fill='black', tag='plot')
            self.canvas.create_line(x, self.height-y, last_x, self.height-last_y, fill='black', tag='plot')
            last_x = x
            last_y = y
        self.canvas.update()


class ToolBar:
    margin = 40
    width = 700
    height = 200

    def __init__(self, generator):
        self.generator = generator
        self.root = Tk()
        self.root.geometry(str(self.width) + 'x' + str(self.height))
        self.root.title("Tool-huyool")

        self.freq_slider = Scale(self.root, orient=HORIZONTAL, length=600,
                                 from_=0, to=150, tickinterval=10)
        self.ampl_slider = Scale(self.root, orient=HORIZONTAL, length=600,
                                 from_=0, to=150, tickinterval=10)
        self.freq_slider.pack()
        self.freq_slider.place(x=self.width-10, y=60, anchor=SE)
        self.freq_slider.set(50)
        self.ampl_slider.pack()
        self.ampl_slider.place(x=self.width-10, y=120, anchor=SE)
        self.ampl_slider.set(50)

        freq_label = Label(self.root, text="Frequency:", font="Arial 14")
        freq_label.pack()
        freq_label.place(x=0, y=20)
        ampl_label = Label(self.root, text="Amplitude:", font="Arial 14")
        ampl_label.pack()
        ampl_label.place(x=0, y=80)

        self.save_btn = Button(self.root, text="Save", width=15, height=3, command=self.save)
        self.save_btn.pack(anchor=CENTER)
        self.save_btn.place(x=self.width//2, y=150, anchor=CENTER)

    def save(self):
        self.generator.amplitude = self.ampl_slider.get()
        self.generator.frequency = self.freq_slider.get()


###  параметры:
###  период, частота, амплитуда


class Generator:
    def __init__(self, plot, frequency=50, amplitude=50):
        self.plot = plot
        self._frequency = frequency
        self._amplitude = amplitude
        self.plot.update_plot(self._frequency, self._amplitude)
        self.value = 0.0

    def generate_value(self):
        while True:
            new_value = self._amplitude * sin(2 * pi * self._frequency * time.time())
            yield new_value

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, new_frequency):
        self._frequency = new_frequency
        self.plot.update_plot(self._frequency, self._amplitude)

    @property
    def amplitude(self):
        return self._amplitude

    @amplitude.setter
    def amplitude(self, new_amplitude):
        self._amplitude = new_amplitude
        self.plot.update_plot(self._frequency, self._amplitude)


def main():
    arr = []
    plot = Plot()
    generator = Generator(plot)
    toolbar = ToolBar(generator)
    try:
        for u in generator.generate_value():
            toolbar.root.update()
            num = round((u+generator.amplitude)/330*256)
            binary = bin(num)[2:]
            binary = '0'*(8-len(binary)) + binary
            bits = list(map(int, list(binary)))
            #for i, pin in enumerate(pins):
            GPIO.output(pins, bits)
            if len(arr) < 100:
                arr.append((u, num, bits))
    except:
        GPIO.cleanup()
        print(arr)


if __name__ == '__main__':
    main()
