from src.core.abonos.calculos import contar_dia_semana_en_mes

#reglas de negocio

# R1: 4 clases -> 20% de descuento
# R2: 5 clases -> 0% de descuento
def descuento_por_clases(cantidad_clases)->float:
    if cantidad_clases == 4:
        return 0.2
    return 0.0

# R3: si contrata después del día 15 → +20%
def descuento_por_fecha(dia_contratacion):
    if dia_contratacion>15:
        return 0.2
    return 0.0

# R4: maximo 30% de descuento sobre el valor del abono
# R6: exceso de descuento -> se acumula.
def calcular_descuento_total(descuento1, descuento2):
    descuentoTotal += descuento1 + descuento2
    
    if descuentoTotal > 0.3:
        exceso = descuentoTotal - 0.3
        return descuentoTotal, exceso
    
    return descuentoTotal, 0.0

# R5: si queda una clase para que termine el mes -> pago completo
def es_ultima_clase_del_mes(clases_restantes:int)->bool:
    return clases_restantes == 1