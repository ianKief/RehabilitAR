def filtrarAsistencias (asistencias, busqueda="", estado='seleccionar_todos', fecha="", solo_comentarios=True):
    lista_final = []
    for asistencia in asistencias:
        if (((busqueda == "") or (busqueda != "" and  asistencia.tieneTexto(busqueda)))
            and asistencia.devolverTrueSiPasaFiltroDeEstado(estado)
            and ((fecha == "") or (fecha != "" and asistencia.esDeFecha(fecha)))
            and ((solo_comentarios == False) or (solo_comentarios == True and asistencia.tieneComentarios()))):
                lista_final.append(asistencia)
    return lista_final

# Soy consciente de que este prototipo es poco eficaz y huele feo