"""
Funciones útiles para el computo y registro en el laboratorio de
carga y descarga de un capacitor.
"""
from typing import List, Tuple
from numbers import Real
from matplotlib.pyplot import plot, style, rcParams, title, xlabel, xticks, ylabel, show, yticks
from pandas import DataFrame
from numpy import log10, polyfit, ndarray, exp, linspace
from numbers import Real


class ResultadoTeorico:
    R = 180 # Ohms
    E = 25 # Volts
    C = 350e-6 # F

    def __init__(self, tiempo: ndarray) -> None:
        self.tiempo = tiempo

    def i_max(self) -> Real:
        return self.E / self.R

    def corrientes(self, carga: bool=True) -> List[Real]:
        i_max = self.i_max()
        if not carga:
            i_max = -self.i_max()
        e = exp(-self.tiempo / (self.R * self.C))
        return i_max * e

    def voltajes(self, carga: bool=True) -> List[Real]:
        if carga:
            return self.E * (1 - exp((-self.tiempo) / (self.R * self.C)))
        return self.E * exp((-self.tiempo) / (self.R * self.C))
    
    def log_vector(self) -> List[Real]:
        return log10(self.corrientes() / self.i_max())

    def constante_tiempo(self) -> Real:
        return - (1 / polyfit(self.log_vector(), self.tiempo, 1)[0])


class ResultadoExperimental:
    def __init__(self, dataframe: DataFrame, carga: bool=True) -> None:
        self.dataframe = dataframe
        self.carga = carga
        ultimo_tiempo = dataframe["t (ms)"].iloc[-1]
        tiempo_teorico = linspace(0, ultimo_tiempo, 50)
        self.teorico = ResultadoTeorico(tiempo_teorico)

    def log_vector(self) -> List[Real]:
        return log10(abs(self.dataframe["Ic (mA)"]) / self.teorico.i_max())
    
    def constante_tiempo(self) -> Real:
        return - (1 / polyfit(self.log_vector(), self.dataframe["t (ms)"], 1)[0])


def crear_tabla(tiempos: List[Real], corrientes: List[Real], voltajes: List[Real]) -> DataFrame:
    return DataFrame(
        {"t (ms)": tiempos, "Ic (mA)": corrientes, "Vc (volts)": voltajes},
        index=range(1, len(tiempos) + 1),
    ).rename_axis("Datos", axis=1)


def up_mil(micro_segundos: float) -> float:
    return micro_segundos * (10 ** -3)


def graficar(titulo: str, resultados: ResultadoExperimental, teorico=False, log=False, y_axis="Ic (mA)", y_label="", color="#3EA6FF") -> None:
    x_axis = "t (ms)"
    y_label = y_axis if y_label == "" else y_label
    dataframe = resultados.dataframe
    y_axis_vector = dataframe[y_axis]

    agregar_teorico(teorico, log, resultados, color)

    if log:
        y_axis_vector = resultados.log_vector()
    plot(dataframe[x_axis], y_axis_vector, color=color, marker="o", markerfacecolor=color, linewidth=0)
    mostrar_grafica(titulo, y_label)


def agregar_teorico(teorico: bool, log: bool, resultados: ResultadoExperimental, color: str) -> None:
    if teorico:
        teorico = resultados.teorico
        y_axis_teorico = teorico.corrientes(resultados.carga)
        if log:
            y_axis_teorico = teorico.log_vector()
        plot(teorico.tiempo, y_axis_teorico, color=color)


def mostrar_grafica(titulo: str, y_axis_label: str) -> None:
    style.use("seaborn-whitegrid")
    rcParams.update({"figure.figsize": (10, 8), "figure.dpi": 100})
    title(titulo)
    xlabel("t (s)")
    ylabel(y_axis_label)
    show()


def error_porcentual(experimental: float, aceptado: float) -> str:
    """
    Calcular error porcentual de un resultado experimental obtenido con
    respecto al aceptado
    """
    porcentaje = abs(((aceptado - experimental) / aceptado) * 100)
    return "{:.8f}%".format(porcentaje)


def resultado_experimentacion(*resultados: ResultadoExperimental) -> DataFrame:
    experimentales = [r.constante_tiempo() for r in resultados]
    aceptados = [r.teorico.constante_tiempo() for r in resultados]
    errores = [error_porcentual(exp, acept) for exp, acept in zip(experimentales, aceptados)]

    return DataFrame({
        "Constante de tiempo": [f"t{i+1}" for i in range(len(resultados))],
        "Experimental (s)": experimentales,
        "Teórico (s)": aceptados,
        "Error Porcentual (%)": errores
    })
