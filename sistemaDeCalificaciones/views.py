from django.shortcuts import render
from django.views.generic import View
from django.shortcuts import redirect, HttpResponse
from sistemaDeCalificaciones.forms import LoginForm, ChangePasswordForm
from sistemaDeCalificaciones.models import *
from django.contrib.auth import login, authenticate, logout
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from datetime import date
from .models import Examen,ExamenAlumno
import os
import sys
import csv
import datetime



def seccion_para_imprimir(seccion):
    materias = Materia.objects.filter(seccion=seccion)
    res = True
    for materia in materias:
            res = res and materia_para_imprimir(materia)
    return res


def materia_para_imprimir(materia):
    trimestres = [1, 2, 3]
    res = True
    for trimestre in trimestres:
        res = res and materia_correcta_en_trimestre(materia, trimestre)
    return res



def prom_primer_trimestre(alumno, materia):
    examen_alumno_promedios = AlumnoMateriaPromedios.objects.filter(alumno=alumno, materia=materia)
    if(len(examen_alumno_promedios) == 0):
        examen_alumno_promedios = AlumnoMateriaPromedios.objects.create(alumno=alumno, materia=materia, primero=0, segundo=0, tercero=0)
        return examen_alumno_promedios.primero
    else:
        return examen_alumno_promedios[0].primero


def prom_segundo_trimestre(alumno, materia):
    examen_alumno_promedios = AlumnoMateriaPromedios.objects.filter(alumno=alumno, materia=materia)
    if(len(examen_alumno_promedios) == 0):
        examen_alumno_promedios = AlumnoMateriaPromedios.objects.create(alumno=alumno, materia=materia, primero=0, segundo=0, tercero=0)
        return examen_alumno_promedios.segundo
    else:
        return examen_alumno_promedios[0].segundo


def prom_tercer_trimestre(alumno, materia):
    examen_alumno_promedios = AlumnoMateriaPromedios.objects.filter(alumno=alumno, materia=materia)
    if(len(examen_alumno_promedios) == 0):
        examen_alumno_promedios = AlumnoMateriaPromedios.objects.create(alumno=alumno, materia=materia, primero=0, segundo=0, tercero=0)
        return examen_alumno_promedios.tercero
    else:
        return examen_alumno_promedios[0].tercero


def prom_anual(alumno, materia):
    import math
    prom = (prom_primer_trimestre(alumno, materia) + prom_segundo_trimestre(alumno, materia) + prom_tercer_trimestre(alumno, materia)) / float(3)
    return math.floor(prom * 100)/100

def get_examenes_del_alumno_en_materia_de_trimestre(alumno,trimestre,materia):
    # obtengo las inscripciones para la seccion a la que pertenece la materia
    """
    inscripciones = Inscripcion.objects.filter(seccion=materia.seccion)
    inscripciones = filter(lambda i : i.fecha_baja == None or i.fecha_baja> datetime.datetime.now().date(), inscripciones)
    alumnos = map(lambda a : a.alumno, inscripciones)
    alumnos = sorted(alumnos, key=lambda a : str.lower(str(a.apellido)))
    """
    return get_dict_examenes(materia, trimestre)



def esPar(numero):
    return numero % 2 == 0


def ordenarPorFecha(examenes):
    return sorted(map(lambda e : e, examenes), key=lambda e : e.fecha)



def get_notas_de(examenes, alumno):
    notas = []
    for examen, alumnos in examenes.iteritems():
        notas.append(alumnos[alumno])
    return sorted(notas, key=lambda e : e.examen.fecha)



def hay_integradora(examenes):
    res = False
    for examen, alumnos in examenes.iteritems():
        res = res or examen.es_integrador
    return res


def promedio_alumno(alumno, examenes):
    notas_de_alumno = get_notas_de(examenes, alumno)
    if len(notas_de_alumno) > 0:
        materia = notas_de_alumno[0].examen.materia
        trimestre = notas_de_alumno[0].examen.trimestre
        examenes_alumno = ExamenAlumno.objects.filter(alumno=alumno, examen__materia=materia, examen__trimestre = trimestre)
        examenes_alumno = filter(lambda e : e.nota != None, examenes_alumno)
        if len(examenes_alumno) > 0:
            # tercer trimestre
            if trimestre == 3:
                integrador = filter(lambda e : e.examen.es_integrador, examenes_alumno)

                # tercer trimestre, con integradora.
                if len(integrador) > 0:
                    notas_no_integradoras = filter(lambda e : not e.examen.es_integrador, examenes_alumno)
                    if len(notas_no_integradoras) > 0:
                        promedio_no_integradoras = round(reduce(lambda x, y : x + y, map(lambda nota: get_nota(nota.nota), notas_no_integradoras)) / float(len(notas_no_integradoras)),2)
                        return int(round((promedio_no_integradoras + integrador[0].nota)/2,0))
                    else:
                        return 0

                # tercer trimestre, sin integradora
                else:
                    return int(round(reduce(lambda x, y : x + y, map(lambda nota: get_nota(nota.nota), examenes_alumno)) / float(len(examenes_alumno)),0))
            # primer y segundo trimestre, sin integradora
            else:
                return int(round(reduce(lambda x, y : x + y, map(lambda nota: get_nota(nota.nota), examenes_alumno)) / float(len(examenes_alumno)),0))
        else:
            return 0
    else:
        return 0


def promedio_alumno_3_notas(alumno, examenes):
    notas_de_alumno = get_notas_de(examenes, alumno)
    if len(notas_de_alumno) > 0:
        materia = notas_de_alumno[0].examen.materia
        trimestre = notas_de_alumno[0].examen.trimestre
        examenes_alumno = ExamenAlumno.objects.filter(alumno=alumno, examen__materia=materia, examen__trimestre = trimestre)
        examenes_alumno = filter(lambda e : e.nota != None, examenes_alumno)
        if len(examenes_alumno) > 0:
            # tercer trimestre
            if trimestre == 3:
                    notas_no_integradoras = filter(lambda e : not e.examen.es_integrador, examenes_alumno)
                    if len(notas_no_integradoras) > 0:
                        promedio_no_integradoras = round(reduce(lambda x, y : x + y, map(lambda nota: get_nota(nota.nota), notas_no_integradoras)) / float(len(notas_no_integradoras)),2)
                        return promedio_no_integradoras
                    else:
                        return 0
            # primer y segundo trimestre, sin integradora
            else:
                return 0
        else:
            return 0
    else:
        return 0

def get_nota(nota):
    if nota == None:
        return 0
    else:
        return nota


def get_estado_de_trimestre(materia, args):
    '''
    :param materia: Una materia
    :param args: 'Clave' ==> puede ser '1' (si se quieren obtener el estado de un trimestre)
    o '2' (si se quiere obtener si el botón debe estar habilitado)
    'Trimestre' ==> Puede ser 1,2 o 3.
    :return: Diccionario (en '1' están los estados de los trimestres. En '2' dice si que botones se habilitan de accesos)
    '''
    arg_list = [arg.strip() for arg in args.split(',')]
    trimestre = arg_list[0]
    clave = arg_list[1]

    institucion = Institucion.objects.all()[0]

    # Estados de los trimestres = Clase bootstrap que va a mostrarse
    estado_primer_trimestre = None
    estado_segundo_trimestre = None
    estado_tercer_trimestre = None

    # Habilitado trimestre = Booleano que indica si tiene que estar habilitada la visibilidad de la materia
    habilitado_primer_trimestre = None
    habilitado_segundo_trimestre = None
    habilitado_tercer_trimestre = None

    if institucion.inicio_de_clases > date.today():
        # Aún no iniciaron las clases
        estado_primer_trimestre = 'fa fa-clock-o'
        estado_segundo_trimestre = 'fa fa-clock-o'
        estado_tercer_trimestre = 'fa fa-clock-o'
        habilitado_primer_trimestre = False
        habilitado_segundo_trimestre = False
        habilitado_tercer_trimestre = False

    elif institucion.inicio_de_clases < date.today() and date.today() < institucion.primer_trimestre:
        # El primer trimestre está en curso
        estado_primer_trimestre = calcular_estado_de_materia(materia, trimestre)
        estado_segundo_trimestre = 'fa fa-clock-o'
        estado_tercer_trimestre = 'fa fa-clock-o'
        habilitado_primer_trimestre = True
        habilitado_segundo_trimestre = False
        habilitado_tercer_trimestre = False

    elif institucion.primer_trimestre < date.today() and date.today() < institucion.segundo_trimestre:
        # El segundo trimestre está en curso
        estado_primer_trimestre = calcular_estado_de_materia(materia, trimestre)
        estado_segundo_trimestre = calcular_estado_de_materia(materia, trimestre)
        estado_tercer_trimestre = 'fa fa-clock-o'
        habilitado_primer_trimestre = False
        habilitado_segundo_trimestre = True
        habilitado_tercer_trimestre = False

    elif institucion.segundo_trimestre < date.today() and date.today() < institucion.tercer_trimestre:
        # El tercer trimestre está en curso
        estado_primer_trimestre = calcular_estado_de_materia(materia, trimestre)
        estado_segundo_trimestre = calcular_estado_de_materia(materia, trimestre)
        estado_tercer_trimestre = calcular_estado_de_materia(materia, trimestre)
        habilitado_primer_trimestre = False
        habilitado_segundo_trimestre = False
        habilitado_tercer_trimestre = True

    else:
        # El ciclo lectivo culminó
        estado_primer_trimestre = calcular_estado_de_materia(materia, trimestre)
        estado_segundo_trimestre = calcular_estado_de_materia(materia, trimestre)
        estado_tercer_trimestre = calcular_estado_de_materia(materia, trimestre)
        habilitado_primer_trimestre = False
        habilitado_segundo_trimestre = False
        habilitado_tercer_trimestre = False

    estados = { '1':{'1':estado_primer_trimestre,'2':estado_segundo_trimestre,'3':estado_tercer_trimestre},
                '2':{'1':habilitado_primer_trimestre, '2':habilitado_segundo_trimestre, '3':habilitado_tercer_trimestre}
              }
    return estados[str(clave)][str(trimestre)]

# --------- fin de filtros --------------


# Funciones helpers

# suma notas que pueden ser None
def sumar_notas(x, y):
    print (x)
    print (y)
    return 0

def calcular_estado_de_materia(materia, trimestre):
    if materia_correcta_en_trimestre(materia, trimestre):
        return 'fa fa-check'
    else:
        return 'fa fa-close'

def materia_correcta_en_trimestre(materia, trimestre):
    '''
    :param materia: Una materia
    :param trimestre: 1,2 o 3
    :return: Retorna un booleano que expresa si todos los alumnos de la materia
    en el trimestre especificado tienen cargadas al menos 3 notas.
    '''

    # Obtengo todos los examens para la materia en el trimestre especificado.
    examenes = len(Examen.objects.filter(materia=materia, trimestre=trimestre))

    # Obtengo todos los alumnos inscriptos a la materia en cuestión.
    alumnos_inscriptos = map(lambda i: i.alumno, filter(lambda i : i.fecha_baja == None or i.fecha_baja> datetime.datetime.now().date(), Inscripcion.objects.filter(seccion=materia.seccion)))

    materia_correcta = True

    for alumno in alumnos_inscriptos:
        if materia_correcta:
            cantidad_de_notas_del_alumno = ExamenAlumno.objects.filter(alumno=alumno, examen__materia=materia, examen__trimestre=trimestre).exclude(nota=None)
            materia_correcta = materia_correcta and len(cantidad_de_notas_del_alumno) >= 3
        else:
            return False
    return materia_correcta

def es_trimestre_editable(trimestre):

    institucion = Institucion.objects.all()[0]

    if institucion.inicio_de_clases > date.today():
        habilitado_primer_trimestre = False
        habilitado_segundo_trimestre = False
        habilitado_tercer_trimestre = False

    elif institucion.inicio_de_clases < date.today() and date.today() < institucion.primer_trimestre:
        # El primer trimestre está en curso
        habilitado_primer_trimestre = True
        habilitado_segundo_trimestre = False
        habilitado_tercer_trimestre = False

    elif institucion.primer_trimestre < date.today() and date.today() < institucion.segundo_trimestre:
        # El segundo trimestre está en curso
        habilitado_primer_trimestre = False
        habilitado_segundo_trimestre = True
        habilitado_tercer_trimestre = False

    elif institucion.segundo_trimestre < date.today() and date.today() < institucion.tercer_trimestre:
        # El tercer trimestre está en curso
        habilitado_primer_trimestre = False
        habilitado_segundo_trimestre = False
        habilitado_tercer_trimestre = True

    else:
        # El ciclo lectivo culminó
        habilitado_primer_trimestre = False
        habilitado_segundo_trimestre = False
        habilitado_tercer_trimestre = False

    trimestres = [habilitado_primer_trimestre, habilitado_segundo_trimestre, habilitado_tercer_trimestre]
    return trimestres[int(trimestre)-1]

# ----------- fin funciones helpers -------------

class VerDetalleView(View):

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        materias = Materia.objects.filter(seccion__pk=kwargs['seccion_pk'])
        return render(request, 'detalle.html', {'materias': materias, 'seccion': Seccion.objects.get(pk=kwargs['seccion_pk'])})

class AnualView(View):

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        materia = Materia.objects.get(pk=kwargs['materia_pk'])
        # obtengo las inscripciones para la seccion a la que pertenece la materia
        inscripciones = Inscripcion.objects.filter(seccion=materia.seccion)
        inscripciones = filter(lambda i : i.fecha_baja == None or i.fecha_baja> datetime.datetime.now().date(), inscripciones)
        alumnos = map(lambda a : a.alumno, inscripciones)
        alumnos = sorted(alumnos, key=lambda a : str.lower(str(a.apellido)))
        return render(request, 'anual.html', {'materia': materia, 'alumnos':alumnos})

class ExamenBorrarView(View):

    @method_decorator(login_required)
    def post(self, request):
        examen = Examen.objects.get(pk=request.POST['examen_pk'])
        examen.delete()
        return redirect('/cursos/' + str(examen.materia.pk) + '/' + str(examen.trimestre))

class ExamenNuevoView(View):

    @method_decorator(login_required)
    def post(self, request):
        materia_pk = request.POST['materia']
        trimestre = request.POST['trimestre']
        nombre = request.POST['nombre']
        observacion = request.POST['observacion']
        fecha = request.POST['fecha']

        if 'es_integrador' in request.POST:
            es_integrador = request.POST['es_integrador']
        else:
            es_integrador = False

        examen = Examen.objects.create(nombre=nombre, materia=Materia.objects.get(pk=materia_pk), trimestre=trimestre, observacion=observacion, fecha=fecha, es_integrador = es_integrador)
        return redirect('/cursos/' + materia_pk + '/' + trimestre)

class ManualView(View):

    def get(self, request):
        return render(request, 'manual.html')

class EstadisticasView(View):

    def get(self, request):
        return render(request, 'estadisticas.html')


class Dudas_profesorView(View):

    def get(self, request):
        preguntas = Preguntas_Profesor.objects.all()
        return render(request, 'dudas_profesor.html', {'preguntas': preguntas})


class Dudas_administradorView(View):

    def get(self, request):
        preguntas = Preguntas_Administrador.objects.all()
        return render(request, 'dudas_administrador.html', {'preguntas' : preguntas})


class Preguntas_frecuentesView(View):

    def get(self, request):
        preguntas = Preguntas_Frecuentes.objects.all()
        return render(request, 'preguntas_frecuentes.html', {'preguntas': preguntas})


class LoginView(View):

    def get(self, request):
        if request.user.is_authenticated():
            return redirect('materias_de_docente')
        else:
            form = LoginForm()
            nombre_institucion = get_institucion_name()
            return render(request, 'login.html', {'form': form, 'nombre_institucion': nombre_institucion})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=User.objects.get(username= request.POST['username']), password=request.POST['password'])
            login(request, user)
            return redirect('materias_de_docente')
        else:
            return render(request, 'login.html', {'form': form})

class DocenteChangePasswordView(View):

    @method_decorator(login_required)
    def get(self, request):
        form = ChangePasswordForm()
        return render(request, 'change_password.html', {'form': form})

    @method_decorator(login_required)
    def post(self, request):
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            new_password = request.POST['password_1']
            user_logged = User.objects.get(username=request.user.username)
            user_logged.set_password(new_password)
            user_logged.save()
            return redirect('login')
        else:
            return render(request, 'change_password.html', {'form': form})

class DocenteResetPasswordView(View):

    def get(self, request):
        return render(request, 'reset_password.html')

class DocenteMateriasView(View):

    @method_decorator(login_required)
    def get(self, request):
        materias = Materia.objects.filter(usuarios__id=request.user.id)
        return render(request, 'materias.html', {'nombre_institucion': get_institucion_name(), 'user': request.user, 'materias': materias})

class LogOutView(View):

    @method_decorator(login_required)
    def get(self, request):
        logout(request)
        return redirect('login')


class CursosView(View):

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):

        trimestre = kwargs['trimestre']
        # obtengo la materia que se quiere visualizar
        materia = Materia.objects.filter(pk=kwargs['materia_pk'])[0]

        # Que el trimestre sea editable depende de la fecha actual.
        #editable = es_trimestre_editable(trimestre)
        editable = True
        # obtengo las inscripciones para la seccion a la que pertenece la materia
        inscripciones = Inscripcion.objects.filter(seccion=materia.seccion)
        inscripciones = filter(lambda i : i.fecha_baja == None or i.fecha_baja> datetime.datetime.now().date(), inscripciones)
        alumnos = map(lambda a : a.alumno, inscripciones)
        alumnos = sorted(alumnos, key=lambda a : str.lower(str(a.apellido)))

        dict_examenes = get_dict_examenes(materia, trimestre)


        return render(request, 'pantalla_cursos.html', {
                                                        'examenes':dict_examenes,
                                                        'alumnos': alumnos,
                                                        'materia':materia,
                                                        'trimestre':trimestre,
                                                        'editable':editable,
                                                        })

class ExamenesAlumnoView(View):

    @method_decorator(login_required)
    def post(self, request):
        import thread
        thread.start_new_thread(guardar_notas, (request,1))
        return redirect('login')

def guardar_notas(request, sleep):
    examenes_alumno = request.POST['examenes_alumno'].split(',')
    notas = request.POST['notas'].split(',')
    if(not (len(examenes_alumno) == 1 and examenes_alumno[0] == u'')): # esto pasa cuando no hay examenes cargados
        alumnos = []
        for index, examen_pk in enumerate(examenes_alumno):
            examen_alumno = ExamenAlumno.objects.get(pk=examen_pk)
            materia = examen_alumno.examen.materia
            nota = notas[index]
            if nota == '' or nota == ' ' or nota == '  ' or int(nota) < 0 or int(nota) > 10:
                examen_alumno.nota = None
            else:
                examen_alumno.nota = nota
            if(not examen_alumno.alumno in alumnos):
                alumnos.append(examen_alumno.alumno)
            trimestre = examen_alumno.examen.trimestre
            examen_alumno.save()
        for alumno in list(set(alumnos)):
             actualizar_promedios(alumno, materia, trimestre)

            # Persisto las notas trimestrales del alumno, para no calcularlas luego.

def actualizar_promedios(alumno, materia, trimestre):
    """
    examen_alumno_promedios = AlumnoMateriaPromedios.objects.filter(alumno=alumno, materia=materia)
    if(len(examen_alumno_promedios) == 0):
        examen_alumno_promedios = AlumnoMateriaPromedios.objects.create(alumno=alumno, materia=materia, primero=0, segundo=0, tercero=0)
    else:
        examen_alumno_promedios = examen_alumno_promedios[0]
    """
    examen_alumno_promedios, created = AlumnoMateriaPromedios.objects.get_or_create(alumno=alumno, materia=materia)
    if trimestre == 1:
        examenes = get_examenes_del_alumno_en_materia_de_trimestre(alumno, 1, materia)
        examen_alumno_promedios.primero = promedio_alumno(alumno, examenes)
    elif trimestre == 2:
        examenes = get_examenes_del_alumno_en_materia_de_trimestre(alumno, 2, materia)
        examen_alumno_promedios.segundo = promedio_alumno(alumno, examenes)
    elif trimestre == 3:
        examenes = get_examenes_del_alumno_en_materia_de_trimestre(alumno, 3, materia)
        examen_alumno_promedios.tercero = promedio_alumno(alumno, examenes)
    examen_alumno_promedios.save()

# Recibe una lista, si ésta contiene un elemento lo retorna, de lo contrario crea un nuevo examen_alumno con los datos que recibe.
def get_or_create_nota(lista, examen, alumno):
    if(len(lista) > 0):
        return lista[0]
    else:
        examen_alumno = ExamenAlumno.objects.create(examen=examen, alumno=alumno, nota=None)
        return examen_alumno

def get_institucion_name():
    institucion = Institucion.objects.all()
    if institucion:
        nombre_institucion = institucion[0].nombre
    else:
        nombre_institucion = "Nombre a completar"
    return nombre_institucion

class ImprimirBoletinesView(View):

    @method_decorator(login_required)
    def get(self, request):
        secciones = Seccion.objects.all()
        return render(request, 'imprimir_boletines.html', {'secciones':secciones})

    @method_decorator(login_required)
    def post(self, request):
        year = datetime.datetime.now().date().year
        trimestre = 1

        # se crea la carpeta que va a contener a los boletines
        folder_name = 'boletines-' + str(year) + '-' + str(trimestre) + '-trimestre'
        if os.path.exists(folder_name):
            import shutil
            shutil.rmtree(folder_name)
        os.mkdir(folder_name)


        inscripciones = Inscripcion.objects.filter(seccion__anio_calendario=year)
        for inscripcion in inscripciones:
            imprimir_boletin(inscripcion, folder_name)
        return redirect('login')

def imprimir_boletin(inscripcion, folder_name):
    print (inscripcion.pk)
    reload(sys)
    sys.setdefaultencoding("latin-1")
    file = open(os.path.join(folder_name, str(inscripcion.alumno.dni) + '.csv'), 'wb')
    wr = csv.writer(file, quoting=csv.QUOTE_ALL)
    wr.writerow(['','','BOLETIN DE CALIFICACIONES'])
    wr.writerow([])
    wr.writerow([])
    wr.writerow(['','Nombre',inscripcion.alumno.primer_nombre])
    wr.writerow(['','Apellido', inscripcion.alumno.apellido])
    wr.writerow(['','Curso',inscripcion.seccion.anio])
    wr.writerow([])
    wr.writerow([])
    wr.writerow(['Materia', 'T1', 'T2', 'T3', 'Pr.', 'Dic.', 'Feb.', 'CEA'])

    materias = Materia.objects.filter(seccion=inscripcion.seccion)
    for materia in materias:
        materia_row = []
        materia_row.append(materia.nombre)
        materia_row.append(get_promedio_de_trimestre(inscripcion.alumno, materia,1))
        materia_row.append(get_promedio_de_trimestre(inscripcion.alumno, materia,2))
        materia_row.append(get_promedio_de_trimestre(inscripcion.alumno, materia,3))

        wr.writerow(materia_row)

    file.close()

def get_promedio_de_trimestre(alumno, materia, trimestre):
    dict_examenes = get_dict_examenes(materia, trimestre)
    return promedio_alumno(alumno, dict_examenes)

class ExportarCursoView(View):

    @method_decorator(login_required)
    def post(self, request):
        file = exportar_curso(request.POST['materia'], request.POST['trimestre'])
        file = open(file.name,"r")
        response = HttpResponse(file.read())
        response["Content-Disposition"]= "attachment; filename=%s" % os.path.split(file.name)[1]
        os.remove(file.name)
        return response

# Guarda en un archivo la planilla del curso y retorna al archivo.
def exportar_curso(materia_pk, trimestre):
    reload(sys)
    sys.setdefaultencoding("latin-1")

    materia = Materia.objects.get(pk=materia_pk)
    trimestre = int(trimestre)

    file = open(str(datetime.datetime.now()) + "-" + str(materia.nombre) + "-" + str(trimestre) + '.csv', 'wb')
    wr = csv.writer(file, quoting=csv.QUOTE_ALL)

    dict_examenes = get_dict_examenes(materia, trimestre)

    wr.writerow([materia.nombre, str(trimestre) + ' trimestre'])
    wr.writerow([])
    wr.writerow(['DNI', 'Nombre','Apellido'])

    # Fila de examenes
    examenes_row = ['','',''] # Estos espacios son por dni, nombre y apellido
    for examen, alumnos in dict_examenes.iteritems():
        examenes_row.append(examen.nombre)
    examenes_row.append('PROMEDIO')
    wr.writerow(examenes_row)
    alumnos = sorted(alumnos, key=lambda a : str.lower(str(a.apellido)))
    for alumno in alumnos:
        alumno_row = []
        alumno_row.append(alumno.dni)
        alumno_row.append(alumno.primer_nombre)
        alumno_row.append(alumno.apellido)
        for nota in get_notas_de(dict_examenes, alumno):
            if nota.nota:
                alumno_row.append(nota.nota)
            else:
                alumno_row.append('')
        alumno_row.append(promedio_alumno(alumno, dict_examenes))
        wr.writerow(alumno_row)
    return file

# este diccionario debe contener todos los examenes y en cada examen un diccionario que sea
# alumno:nota (deben estar todos los alumnos)
def get_dict_examenes(materia, trimestre):
    # obtengo las inscripciones para la seccion a la que pertenece la materia
    inscripciones = Inscripcion.objects.filter(seccion=materia.seccion)

    # obtengo todos los examenes para esta materia
    examenes = Examen.objects.filter(materia=materia, trimestre=trimestre)

    dict_examenes = {}
    for examen in examenes:
        dict_alumnos = {}
        for inscripcion in inscripciones:
            dict_alumnos[inscripcion.alumno] = get_or_create_nota(ExamenAlumno.objects.filter(examen=examen, alumno=inscripcion.alumno), examen, inscripcion.alumno)
            dict_examenes[examen] = dict_alumnos
    return dict_examenes
