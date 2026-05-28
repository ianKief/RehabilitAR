from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from sqlalchemy import select
from sqlalchemy.orm import aliased

from datetime import timedelta

"Reglas"
#R1: la activacion del abono dura un mes, si la fecha contr. es 31 -> dura hasta el ult. dia del sig. mes 
def duracion_abono_mensual(fecha_contratacion:date):
    nueva_fecha=fecha_contratacion+relativedelta(months=1)
    return nueva_fecha


#R2: obtiene 20% de descuento si la cant. dias es 4
#R3: no obtiene descuento si la cant. dias es superior a 4
def calcular_descuento_automatico(cantidad_dias):
    if cantidad_dias == 4:
        return 0.2
    return 0.0

#R4: el valor de la clase es dias * valor clase
def valor_abono_mensual(cantidad_dias,valor_clase):
    return cantidad_dias*valor_clase

def contar_dias_semana(dia_semana,fecha_inicio:date,fecha_fin:date):
    contador=0
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        if fecha_actual.weekday() == dia_semana:
            contador+=1
        fecha_actual+=timedelta(days=1)
    return contador

def calcular_valor_abono(dia_semana_elegido):
    fecha = date.today()

    dias = contar_dias_semana(
        dia_semana_elegido,
        fecha,
        duracion_abono_mensual(fecha)
    )

    valor = valor_abono_mensual(dias,obtener_precio_clase_actual())*(1-calcular_descuento_automatico(dias))

    return valor