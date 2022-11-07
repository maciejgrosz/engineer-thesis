import threading
import tkinter as ttk
import re
import pandas as pd
import numpy as np
from PIL import Image, ImageTk
from itertools import count
from scipy.signal import savgol_filter
from datetime import date
import serial


class Prox(ttk.Entry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.var = ttk.StringVar(master)
        self.var.trace("w", self.validate)
        ttk.Entry.__init__(self, master, textvariable=self.var, **kwargs)
        self.get, self.set = self.var.get, self.var.set

    def validate(self):
        value = self.get()
        if not value.isdigit():
            self.set("".join(x for x in value if x.isdigit()))


def clicked(a, b, c):
    if len(a.get()) == 0 or len(b.get()) == 0 or len(c.get()) == 0:
        popupmsg("Wprowadź poprawne dane!")
    else:
        global keepGoing
        keepGoing = True
        th = threading.Thread(
            target=readData, args=(float(a.get()), float(b.get()), float(c.get()))
        )
        th.daemon = True
        th.start()


def popupmsg(msg):
    popup = ttk.Tk()
    popup.wm_title("ERROR")
    label = ttk.Label(popup, text=msg)
    label.pack(side="top", fill="x", pady=10)
    B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
    B1.pack()
    popup.mainloop()


def clean():
    with open("przyspieszenie.txt", "a") as file:
        file.truncate(0)
        file.close()
    with open("predkosc.txt", "a") as file1:
        file1.truncate(0)
        file1.close()
    with open("przemieszczenie.txt", "a") as file3:
        file3.truncate(0)
        file3.close()
    with open("moc.txt", "a") as file4:
        file4.truncate(0)
        file4.close()


def stop():
    global keepGoing
    keepGoing = False


def smoothing(file, size):
    i = 0
    setlist = []
    result = ""
    with open(file, "r") as file1:
        for line in file1:
            inner_list = [elt.strip() for elt in line.split(",")]
            setlist.append(float(inner_list[1]))
    yhat = savgol_filter(setlist, size, 3)
    with open(file, "r") as file2:
        for line in file2:
            list = line.split(",")
            list[1] = str(yhat[i])
            line = ",".join(list)
            result += line + "\n"
            i = i + 1
    f = open(file, "w")
    f.write(result)
    f.close()


def export(mcz, mo, wz):
    today = date.today()
    d1 = today.strftime("%b-%d-%Y")
    df = pd.merge(
        exportDislocation(), exportVelocity(), left_on=["seria"], right_on=["seria"]
    ).drop(columns=["Czas_x", "Czas_y"])
    df = df.merge(exportAcceleration(), left_on=["seria"], right_on=["seria"])
    df = df.merge(exportPower(), left_on=["seria"], right_on=["seria"]).drop(
        columns=["Czas_x", "Czas_y"]
    )
    df.to_csv(r"{0}_{1}_{2}_{3}".format(mcz.get(), mo.get(), wz.get(), d1))


def exportVelocity():
    time = []
    velocity = []
    with open("predkosc1.txt") as f:
        for line in f:
            time.append(float(line.split(",")[0]))
            velocity.append(float(line.split(",")[-1]))
    d = {"Predkosc": velocity, "Czas": time}
    df = pd.DataFrame(d)
    df1 = pd.DataFrame(d)
    df3 = pd.DataFrame(d)
    df3[df3.Predkosc < 0] = 0
    minSample = df["Predkosc"].min()
    maxSample = df["Predkosc"].max()
    gap = maxSample - minSample
    normalized_sample = (df["Predkosc"] - minSample) / gap
    df3["Predkosc"] = normalized_sample
    normalized_sample = (normalized_sample - 0.5) * 2
    df["Predkosc"] = normalized_sample
    booleans = df.Predkosc > 0.8
    booleans.tolist()
    a = booleans[0]
    start = []
    end = []
    for idx, item in enumerate(booleans):
        if item != a and item == True:
            start.append(idx)
        elif item != a and item == False:
            end.append(idx)
        a = item
    for idx, items in enumerate(start):
        df1.loc[items : end[idx], "seria"] = idx + 1
    df2 = df1.groupby(["seria"]).max()
    booleans1 = df3.Predkosc > 0.01
    booleans1.tolist()
    a1 = booleans1[0]
    start1 = []
    end1 = []
    for idx, item in enumerate(booleans1):
        if item != a1 and item == True:
            start1.append(idx)
        elif item != a1 and item == False:
            end1.append(idx)
        a1 = item
    for idx, items in enumerate(start):
        df3.loc[items : end[idx], "seria"] = idx + 1
    df4 = df3.groupby(["seria"]).mean()
    df4 = df4.rename(columns={"Predkosc": "Srednia predkosc"})
    df5 = pd.merge(df2, df4, left_on=["seria"], right_on=["seria"])
    return df5


def exportAcceleration():
    time = []
    acceleration = []
    with open("przyspieszenie.txt") as f:
        for line in f:
            time.append(float(line.split(",")[0]))
            acceleration.append(float(line.split(",")[-1]))
    d = {"Przyspieszenie": acceleration, "Czas": time}
    df = pd.DataFrame(d)
    df1 = pd.DataFrame(d)
    minSample = df["Przyspieszenie"].min()
    maxSample = df["Przyspieszenie"].max()
    gap = maxSample - minSample
    normalized_sample = (df["Przyspieszenie"] - minSample) / gap
    normalized_sample = (normalized_sample - 0.5) * 2
    df["Przyspieszenie"] = normalized_sample
    booleans = df.Przyspieszenie > 0.8
    booleans.tolist()
    a = booleans[0]
    start = []
    end = []
    for idx, item in enumerate(booleans):
        if item != a and item == True:
            start.append(idx)
        elif item != a and item == False:
            end.append(idx)
        a = item
    for idx, items in enumerate(start):
        df1.loc[items : end[idx], "seria"] = idx + 1
    df2 = df1.groupby(["seria"]).max()
    return df2


def exportPower():
    time = []
    power = []
    with open("moc.txt") as f:
        for line in f:
            time.append(float(line.split(",")[0]))
            power.append(float(line.split(",")[-1]))
    d = {"Moc": power, "Czas": time}
    df = pd.DataFrame(d)
    df1 = pd.DataFrame(d)
    minSample = df["Moc"].min()
    maxSample = df["Moc"].max()
    gap = maxSample - minSample
    normalized_sample = (df["Moc"] - minSample) / gap
    normalized_sample = (normalized_sample - 0.5) * 2
    df["Moc"] = normalized_sample
    booleans = df.Moc > 0.8
    booleans.tolist()
    a = booleans[0]
    start = []
    end = []
    for idx, item in enumerate(booleans):
        if item != a and item == True:
            start.append(idx)
        elif item != a and item == False:
            end.append(idx)
        a = item
    for idx, items in enumerate(start):
        df1.loc[items : end[idx], "seria"] = idx + 1
    df2 = df1.groupby(["seria"]).max()
    return df2


def exportDislocation():
    time = []
    dislocation = []
    with open("przemieszczenie.txt") as f:
        for line in f:
            time.append(float(line.split(",")[0]))
            dislocation.append(float(line.split(",")[-1]))
    d = {"Przemieszczenie": dislocation, "Czas": time}
    df = pd.DataFrame(d)
    df1 = pd.DataFrame(d)
    duplicate = pd.DataFrame(d)
    duplicate = duplicate.duplicated(["Przemieszczenie"])
    duplicate.to_csv(r"testy.csv")
    lista = df1.Przemieszczenie.tolist()
    minSample = df["Przemieszczenie"].min()
    maxSample = df["Przemieszczenie"].max()
    gap = maxSample - minSample
    normalized_sample = (df["Przemieszczenie"] - minSample) / gap
    normalized_sample = (normalized_sample - 0.5) * 2
    df["Przemieszczenie"] = normalized_sample
    booleans = df.Przemieszczenie < -0.8
    booleans.tolist()
    a = booleans[0]
    start = []
    end = []
    for idx, item in enumerate(booleans):
        if item != a and item == True:
            start.append(idx)
        elif item != a and item == False:
            end.append(idx)
        a = item
    for idx, items in enumerate(start):
        df1.loc[items : end[idx], "seria"] = idx + 1
    df2 = df1.groupby(["seria"]).min()
    ar = df2.Przemieszczenie.tolist()
    df2 = df2 * -1
    arboolean = []
    aridx = []
    arvalue = []
    arvalue2 = []
    a = 0
    for idx1, item1 in enumerate(lista):
        if idx1 == 0:
            arboolean.append(False)
        else:
            if a == 2:
                print(lista[idx1])
                print(arboolean[-1])
            if lista[idx1] != ar[a] and arboolean[-1] == False:
                arboolean.append(False)
            elif lista[idx1] > ar[a] and arboolean[-1] == True:
                if lista[idx1] >= lista[idx1 - 1]:
                    arboolean.append(True)
                else:
                    arboolean.append(False)
                    aridx.append(idx1 - 1)
                    v1 = (ar[a] - lista[idx1 - 1]) * -1
                    arvalue2.append(lista[idx1 - 1])
                    arvalue.append(v1)
                    if len(ar) - 1 > a:
                        a = a + 1
                    else:
                        arboolean.append(True)
    print(arvalue)
    print(arvalue2)
    print(ar)
    df2.Przemieszczenie = arvalue
    return df2.drop(columns="Czas")


def readData(m1, m2, h1):  # m1 - masa ciezaru, m2-masa miesni h1-dlugosc ciala
    try:
        arduinoData = serial.Serial("/dev/ttyACM0", timeout=1)
    except:
        print("Please check the port")
    clean()
    timestamp = str(serial.time.time())
    count = 0
    rawdata = []
    P = []
    J = 0.000193152  # moment bezwładnosci krazka podany w kg*m^2
    r = 0.0625  # promien krazka w m +
    m_sum = (
        7.4484 + 0.76694 * m2 - 0.05192 * h1 + m1
    )  # dla masy ciala 80, ciezaru 50, wzrost 180 - 109,458kg
    g = 9.81  # przyspieszenie ziemnskie w m/s^2
    A = J + (m_sum * r**2)
    B = m_sum * g * r
    Fsmyczy = 150 / 1000 * g
    C = Fsmyczy * r
    fik = 0  # fi aktualne
    fik_1 = 0  # fi poprzednie
    fik_2 = 0  # fi poprzednie (fi akutalne -2)
    t_s = 0.01  # czas probkowania w sek
    P_lift = 0
    fikakt = 0
    fik_pop = 0
    fik_poppop = 0
    t = 0
    t1 = 0
    tc = 0
    v = 0
    i = 0
    a = 0
    while keepGoing:
        c = [
            float(s) for s in re.findall("\\d+", str(arduinoData.readline()))
        ]  # Wczytanie outputu z arduino
    if c:
        i = i + 1
        # OBLICZENIA
        fik_poppop = fik_pop
        fik_pop = fikakt
        fikakt = c[-1]
        fik_2 = fik_1
        fik_1 = fik
        fik = ((c[-1] - 1000) / 200) * 3.14  # odczyt kąta w radianach
        t1 = t
        t = c[0] / 1000
        t_s = t - t1
        if t_s > 1 or t_s == 0 or t_s < 0.0001:
            t_s = 0.01
        v1 = v
        v = (fik - fik_1) * r / t_s
        a1 = a
        a = (v - v1) / t_s
        tc = tc + t_s
        fi_prim = (fik - fik_1) / t_s  # pierwsza pochodna kąta
        fi_bis = (fik - 2 * fik_1 + fik_2) / (t_s**2)  # druga pochodna kąta
        P_lift = (
            A * fi_prim * fi_bis + B * fi_prim + C * fi_prim
        )  # moc całkowita wyrażona w W
    with open("przemieszczenie.txt", "a") as file:
        file.write("{},{}\n".format(tc, fik * r))
        file.close()
    with open("predkosc.txt", "a") as file1:
        file1.write("{},{}\n".format(tc, v))
        file1.close()
    with open("przyspieszenie.txt", "a") as file2:
        file2.write("{},{}\n".format(tc, a))
        file2.close()
    with open("moc.txt", "a") as file3:
        file3.write("{},{}\n".format(tc, P_lift))
        file3.close()
