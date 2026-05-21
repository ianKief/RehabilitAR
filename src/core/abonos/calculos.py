from datetime import date, timedelta
import calendar
#esto se encarga de funciones puras(matematicas/reglas simples) 

def contar_dia_semana_en_mes(anio:int, mes:int, dia_semana:int)->int:
    fecha=_obtener_primer_dia_coincidente(anio, mes, dia_semana)
    return _contar_dias_del_mes(fecha,mes)


def _obtener_primer_dia_coincidente(anio:int, mes:int, dia_semana:int)->date:
    # me muevo hasta al dia de la semana elegido
    fecha=date(anio,mes, 1)
    while fecha.weekday()!= dia_semana:
        fecha+=timedelta(days=1)
    return fecha

def _contar_dias_del_mes(fecha: date, mes:int) -> int:
    
    #cuento las veces que aparece el dia ingresado saltando de 7 en 7
    cantidad_dias=0
    while fecha.month == mes:
        cantidad_dias+=1
        fecha+=timedelta(days=7) # esto representa el salto de 7 dias

    # retorno la cantidad de veces del dia
    return cantidad_dias

def contar_clases_faltantes(anio, mes, dia_semana):
    
    hoy = date.today()

    ultimo_dia_del_mes = calendar.monthrange(anio,mes)[1]

    clasesFaltante=0

    for dia in range(hoy, ultimo_dia_del_mes+1):
       fecha = date(anio, mes, dia)

       if fecha.weekday()==dia_semana:
           clasesFaltante+=1
    
    return clasesFaltante

 

