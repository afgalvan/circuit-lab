"""
Funciones útiles para el computo y registro en el laboratorio de
carga y descarga de un capacitor.
"""
from typing import List, Tuple
from numbers import Real
from matplotlib.pyplot import plot, style, rcParams, title, xlabel, xticks, ylabel, show, yticks
from pandas import DataFrame
from numpy import polyfit, ndarray, exp, linspace
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


class ResultadoExperimental:
    def __init__(self, dataframe: DataFrame, carga: bool=True) -> None:
        self.dataframe = dataframe
        self.carga = carga
        ultimo_tiempo = dataframe["t (ms)"].iloc[-1]
        tiempo_teorico = linspace(0, ultimo_tiempo, 50)
        self.teorico = ResultadoTeorico(tiempo_teorico)


def crear_tabla(tiempos: List[Real], corrientes: List[Real], voltajes: List[Real]) -> DataFrame:
    return DataFrame(
        {"t (ms)": tiempos, "Ic (mA)": corrientes, "Vc (volts)": voltajes},
        index=range(1, len(tiempos) + 1),
    ).rename_axis("Datos", axis=1)


def up_mil(micro_segundos: float) -> float:
    return micro_segundos * (10 ** -3)


def graficar(titulo: str, resultados: ResultadoExperimental, teorico=False, y_axis: str="Ic (mA)", color: str="#3EA6FF") -> None:
    x_axis = "t (ms)"
    dataframe = resultados.dataframe
    style.use("seaborn-whitegrid")

    if teorico:
        teorico = resultados.teorico
        corrientes = teorico.corrientes(resultados.carga)
        plot(teorico.tiempo, corrientes, color=color)
    plot(dataframe[x_axis], dataframe[y_axis], color=color, marker="o", markerfacecolor=color, linewidth=0)
    rcParams.update({"figure.figsize": (10, 8), "figure.dpi": 100})
    title(titulo)
    xlabel("t (s)")
    ylabel("Ic (A)")
    show()


def error_porcentual(aceptado: float, experimental: float) -> str:
    """
    Calcular error porcentual de un resultado experimental obtenido con
    respecto al aceptado
    """
    porcentaje = abs(((aceptado - experimental) / aceptado) * 100)
    return "{:.8f}%".format(porcentaje)


def calcular_tiempo(dataframe: DataFrame) -> Tuple[Real, Real]:
    resitencia_experimental = polyfit(dataframe["Ic (mA)"], dataframe["Vc (volts)"], 1)[0]
    resistencia_teorica = dataframe["Vc (volts)"].iloc[-1] / dataframe["Ic (mA)"].iloc[-1]
    return (resitencia_experimental, resistencia_teorica)


def resultado_experimentacion(*dataframes: DataFrame) -> DataFrame:
    resultados = [calcular_tiempo(d) for d in dataframes]
    experimentales = map(lambda x: x[0], resultados)
    aceptados = map(lambda x: x[1], resultados)
    errores = [error_porcentual(acept, exp) for exp, acept in resultados]

    return DataFrame({
        "Constante de tiempo": [f"t{i+1}" for i in range(len(resultados))],
        "Experimental": experimentales,
        "Teórico": aceptados,
        "Error Porcentual": errores
    })
