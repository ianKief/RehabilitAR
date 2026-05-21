from datetime import date
from src.core.abonos.reglas import (
    descuento_por_clases,
    descuento_por_fecha,
    es_ultima_clase_del_mes,
    calcular_descuento_total
)
from src.core.abonos.calculos import (
    contar_clases_faltantes,
    contar_dia_semana_en_mes
)
# orquestador (logica principal)

def calcular_abono_mensual(anio:int, mes:int, dia_semana: int,fecha_contratacion:date,valor_abono:float ):
    
    clases_restantes = contar_clases_faltantes(anio,mes,dia_semana)

    if es_ultima_clase_del_mes(clases_restantes):
        return _armar_retorno(valor_abono=valor_abono,
        descuento=0.0,
        clases_restantes=clases_restantes,
        tipo="SIN_DESCUENTO_ULTIMA_CLASE")
    
    resultado=_calcular_valor_abono(anio,mes,dia_semana,fecha_contratacion,valor_abono)
    
    return _armar_retorno(
        valor_abono=resultado["monto_final"],
        descuento=resultado["descuento_total"],
        clases_restantes=clases_restantes,
        tipo="Normal")

def _calcular_valor_abono(anio, mes, dia_semana, dia_contratacion, valor):
    d1=descuento_por_clases(contar_dia_semana_en_mes(anio,mes,dia_semana))
    d2=descuento_por_fecha(dia_contratacion)

    descuentoTotal,saldo=calcular_descuento_total(d1,d2)

    monto_final=valor*(1-descuentoTotal)
    return{"descuento_total":descuentoTotal,
           "saldo":saldo,
           "monto_final":monto_final}


def _armar_retorno(valor_abono,descuento,clases_restantes, tipo):
    return {
            "monto_final": valor_abono,
            "descuento_total":descuento,
            "tipo":tipo,
            "clases_disponibles":clases_restantes
        }


