#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
from daemon import runner
import os
import sys
import ConfigParser
import android
#import RPi.GPIO as pi


class ubicaText():
    def __init__(self):

        self.nombreArchivoConf = 'ubicame.cfg'
        self.fc = ConfigParser.ConfigParser()

        #Propiedades de la Clase
        self.archivoLog = ''
        
        #Para saber como se llama este archivo .py que se esta ejecutando
        archivo = sys.argv[0]  # Obtengo el nombre de este  archivo
        archivoSinRuta = os.path.basename(archivo)  # Elimino la Ruta en caso de tenerla
        self.archivoActual = archivoSinRuta

        self.configInicial()
        self.parametrosTelefono()
        self.configDemonio()

    def configInicial(self):
        '''Metodo que permite extraer todos los parametros
        del archivo de configuracion ubicame.cfg que se
        utilizara en todo el script'''

        #Obtiene Informacion del archivo de Configuracion .cfg
        self.ruta_arch_conf = os.path.dirname(sys.argv[0])
        self.archivo_configuracion = os.path.join(self.ruta_arch_conf, self.nombreArchivoConf)
        self.fc.read(self.archivo_configuracion)
        
        #Obtiene el nombre del archivo .log para uso del Logging
        seccion = 'RUTAS'
        opcion = 'archivo_log'
        self.archivoLog = self.fc.get(seccion, opcion)
        
    def parametrosTelefono(self):
        ''' Obtener los valores de configuracion del Telefono
            del archivo .cfg'''

        lista = self.fc.items('GSM') 
        
        self.ip_telefono, \
        self.puerto_telefono, \
        self.puerto_adb_forward, \
        self.serial_telefono = [valor[1] for valor in lista]

    def configDemonio(self):
        '''Configuiracion del Demonio'''

        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  '/tmp/{0}.pid'.format(self.archivoActual)
        self.pidfile_timeout = 5
       
    def configLog(self):
        '''Metodo que configura los Logs de error tanto el nombre
        del archivo como su ubicacion asi como tambien los 
        metodos y formato de salida'''
        
        #Extrae de la clase la propiedad que contiene el nombre del archivo log
        nombreArchivoLog = self.archivoLog
        self.logger = logging.getLogger("{0}".format(self.archivoActual))
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(levelname)s--> %(asctime)s - %(name)s:  %(message)s", datefmt='%d/%m/%Y %I:%M:%S %p')
        handler = logging.FileHandler(nombreArchivoLog)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        return handler

    def gps(self, evento):
        ''' Metodo que permite obtener las coordenadas del GPS del celular
        y regresar Latitud y Longitud'''

        terminar = False
        segundos = 120
        segTranscurridos = 0
        pos = [0, 0]
        mensaje = ''
        mapa = ''
        smsDevolver = ''

        self.droid.startLocating(3600,1)
        time.sleep(10)
        while not terminar:
            segTranscurridos+=1
            ubicacion = self.droid.readLocation()
            ubi = ubicacion.result
            
            if "gps" in ubi:
                mensaje = u"Posición actual: "
                pos = (str(ubi["gps"]["latitude"]), str(ubi["gps"]["longitude"]))
                terminar = True
            else:
                if "network" in ubi:
                    pos = (str(ubi["network"]["latitude"]), str(ubi["network"]["longitude"]))
                    mensaje = u"Posicion red celular: "
                    terminar = True
                else:
                    lll = self.droid.getLastKnownLocation().result
                    if "network" in lll:
                        if lll['network']:
                            pos = (str(lll["network"]["latitude"]), str(lll["network"]["longitude"]))
                            mensaje = u"Ultima posicion red celular: "
                        else:
                            pos = [0, 0]
                            mensaje = "No se pudo obtener la Ultima posicion de red celular"
                    else:
                        pos = [0, 0]
                        mensaje = "No se pudo obtener la Ultima posicion de red celular"

            if segTranscurridos >= segundos:
                terminar = True
        
        pll = "{0},{1}".format(str(pos[0]), str(pos[1]))
        mapa = "http://maps.google.com/maps?ll=%s&q=%s" % (pll, pll)
        smsDevolver = '{0} {1}'.format(mensaje, mapa)
        self.droid.stopLocating()
        return smsDevolver

    def raspberryAbrir(self):
        ''' metodo para envio de señal al selenoide'''
        pi.cleanup()
        pi.setmode(pi.BOARD)
        pi.setup(11, pi.OUT)
        pi.output(11, True)

    def verificaSms(self, numero, parametros):
        ''' Verifica si los parametros pasados en el sms
        son correctos, valor de entrada:
            (numeroTelefono, smsBandejaEntrada)'''

        self.parametros = parametros
        mensaje = self.parametros.split()
        self.numero = numero
        listaAutorizados = [auto[1] for auto in self.fc.items('AUTORIZADOS')]
        param2 = ''
        param3 = mensaje[2] if len(mensaje) == 3 else ''
        comandoDevolver = ''
        metodoDevolver = ''
        ejecutarMetodo = ''
        error = True

        #Verifica si el numero telefonico esta autorizado para enviar comandos
        if numero in listaAutorizados or param3 in listaAutorizados:
            #Si Longitud es 1, es decir que se envio un comando si su evento
            if len(mensaje) == 1:
                comando = mensaje[0].lower()
                #Verifico si Existe la OPCION "Comando" en los EVENTOS del archivo .cfg
                if self.fc.has_option('EVENTOS', comando):
                    #Verifico que el comando necesita un evento Ej on
                    if self.fc.get('EVENTOS', comando):
                        error, comandoDevolver = True, 'El Comando:{0} necesita un paremetro adicional,\
                        Ej: LUCES ON'.format(comando)
                else:
                    error, comandoDevolver = True, 'El Comando:{0} no Existe, escriba un comando valido'.\
                            format(comando)
            
            #Si Longitud es 2, es decir que se envio un comando con su evento
            elif len(mensaje) == 2:
                comando, param2 = mensaje
                if self.fc.has_option('EVENTOS', comando):
                    valorEventos = self.fc.get('EVENTOS', comando).split(',')
                    if param2.lower() in valorEventos:
                        if self.fc.has_option('METODOS', comando):  # Si existe la opcion dentro de la seccion
                            #Obtengo el nombre del metodo asociado al comando pasado
                            ejecutarMetodo = fc.get('METODOS', comando)  
                            if ejecutarMetodo:  # Si la opcion "comando" pasada  tiene un valor dentro de la seccion METODO
                                error, comandoDevolver, metodoDevolver = False, self.parametros, ejecutarMetodo
                            else:
                                error, comandoDevolver = True, 'La opcion {0} dentro de la seccion "METODOS" no \
                                        tiene ningun valor asignado dentro del archivo de configuracion .fcg'.format(comando)
                        else:
                            error, comandoDevolver = True, 'El Comando:{0} no contiene ningun metodo llamado:{1}'\
                                    .format(comando, ejecutarMetodo)
                    else:
                        error, comandoDevolver = True, 'El Comando:{0} no contiene el Parametro:{1}'.format(
                            comando, param2)
                else:
                    error, comandoDevolver = True, 'El Comando:{0} no Existe, escriba un comando valido'.format(comando)
            
            #Si Longitud es 3, es decir que se envio un comando con su evento y una clave
            elif len(mensaje) == 3:
                comando, param2, param3 = mensaje
                if self.fc.has_option('EVENTOS', comando):
                    valorEventos = self.fc.get('EVENTOS', comando).split(',')
                    if param2.lower() in valorEventos:
                        if self.fc.has_option('METODOS', comando):  # Si existe la opcion dentro de la seccion
                            #Obtengo el nombre del metodo asociado al comando pasado
                            ejecutarMetodo = fc.get('METODOS', comando)
                            if ejecutarMetodo:  # Si la opcion "comando" pasada  tiene un valor dentro de la seccion METODO
                                error, comandoDevolver, metodoDevolver = False, comando + ' ' + param2, ejecutarMetodo
                            else:
                                error, comandoDevolver = True, 'La opcion {0} dentro de la seccion "METODOS" no \
                                        tiene ningun valor asignado dentro del archivo de configuracion .fcg'.format(comando)
                        else:
                            error, comandoDevolver = True, 'El Comando:{0} no contiene ningun metodo llamado:{1}'\
                                    .format(comando, ejecutarMetodo)
                    else:
                        error, comandoDevolver = True, 'El Comando:{0} no contiene el Parametro:{1}'.format(
                            comando, param2)
                else:
                    error, comandoDevolver = True, 'El Comando:{0} no Existe, escriba un comando valido'.format(comando)
            
            #Si Longitud es 3, es decir que se envio un comando con su evento y una clave
            elif len(mensaje) >3:
                error, comandoDevolver = True, 'Demasiados Parametros'
        else:
            error, comandoDevolver = True, 'Telefono no esta Autotizado o Contraseña Invalida'
        return error, comandoDevolver, metodoDevolver

    def smsProcesar(self, registros):
        ''' Metodo que recibe un listado de sms que se encuentran en bandeja de entrada
        del telefono celular y permite clasificarlos segun su peticion, bien sea para
        obtener la posicion GPS o abrir las puertas del vehiculo'''
        #print(registros)
        for fila in registros:
            id, numero, cuerpo = fila
            error, sentencia, metodo = self.verificaSms(numero, cuerpo)
            if not error:
                comando, evento, metodo = sentencia.split()
                metodo2 = '{0}({1})'.format(metodo, evento)
                print(metodo2)
                #mensaje = self.gps(evento)
                #self.logger.info('Mensaje enviado a:{0} --> {1}'.format(numero, mensaje))
                #self.smsEnviar(id, numero, mensaje)
                
                #elif comando.upper() == 'REINICIAR_TELEFONO':
                #    self.reiniciarTelefono()
                #    self.conectarAndroid()
            else:
                self.logger.error('Mensaje enviado a: {0} --> {1}'.format(numero, sentencia))
                self.smsEnviar(id, numero, sentencia)

    def smsProcesarOld(self, registros):
        ''' Metodo que recibe un listado de sms que se encuentran en bandeja de entrada
        del telefono celular y permite clasificarlos segun su peticion, bien sea para
        obtener la posicion GPS o abrir las puertas del vehiculo'''
        #print(registros)
        for fila in registros:
            id, numero, cuerpo = fila
            ejecutar, sentencia = self.verificaSms(numero, cuerpo)
            if not ejecutar:
                comando, evento = sentencia.split()
                if comando.upper() == 'GPS':
                    mensaje = self.gps(evento)
                    self.logger.info('Mensaje enviado a:{0} --> {1}'.format(numero, mensaje))
                    self.smsEnviar(id, numero, mensaje)

                elif comando.upper() == 'MOTOR':
                    mensaje = self.motor(evento)
                    
                elif comando.upper() == 'PUERTAS':
                    mensaje = self.puertas(evento)
                    
                elif comando.upper() == 'LUCES':
                    mensaje = self.luces(evento)
                    
                elif comando.upper() == 'CORNETA':
                    mensaje = self.corneta(evento)

                elif comando.upper() == 'REINICIAR_TELEFONO':
                    self.reiniciarTelefono()
                    self.conectarAndroid()
            else:
                self.logger.error('Mensaje enviado a: {0} --> {1}'.format(numero, sentencia))
                self.smsEnviar(id, numero, sentencia)
    
    def smsEnviar(self, id, numero, mensaje):
        '''Metodo para enviar los SMS a los Usuarios '''
        self.id = id
        self.numeroTlf = numero
        self.mensaje = mensaje
        self.droid.smsSend(self.numeroTlf, self.mensaje)
        self.droid.smsMarkMessageRead([self.id], True)

    def smsRecibidos(self):
        ''' Metodo que permite buscar los SMS enviados por los
         en bandeja de entrada pacientes y guardarlos en una lista 
         para luego ser procesados
         Valor de retorno: (id, telefono, sms)
        '''
                
        listaDevolver = []      
        try:
            msg_solicitud = self.droid.smsGetMessages(True)                
            #Se recorre la lista de los SMS en el telefono
            #Y se toma solo el ID y el Numero
            for i in msg_solicitud.result:
                id = i['_id']
                telefono = i['address']
                sms = i['body']  # Para versiones Futuras el texto del SMS
                listaDevolver.append((id, telefono, sms))
        except:
            self.logger.error('Error al momento de obtener los SMS en la bandeja de entrada del Telefono Android')
        return listaDevolver

    def sms(self):
        ''' Metodo para procesar todo lo referente a peticiones hechas via sms'''

        self.conectarAndroid()
        smsListaR = self.smsRecibidos()
        self.smsProcesar(smsListaR)
        
    def bluetooh(self):
        pass

    def conectarAndroid(self):
        ''' Metodo que permite recorrer el archivo de configuracion .cfg
        y buscar los telefonos Android conectados via usb para instanciarlos
        para poder obtener los sms en bandeja de entrada'''

        os.system('adb -s {0} wait-for-device'.format(self.serial_telefono))
        try:
            self.droid = android.Android((self.ip_telefono, self.puerto_adb_forward))            
        except:
            self.logger.error('No se pudo Conectar con el Telefono Servidor Android')    
            self.logger.warning('Redirigiendo el Puerto debido a un error al momento de intentar conectar el telefono Android')
            os.system('adb -s {0} forward tcp:{1} tcp:{2}'.format(self.serial_telefono, self.puerto_adb_forward, self.puerto_telefono))
            time.sleep(3)

    def reiniciarTelefono(self):
        '''Metodo que permite reinciar el telefono android
        y levantar automaticamente SL4A asi como tambien
        redireccionar el puerto adb'''
        
        self.logger.warning('Reiniciando el telefono...!')
        os.system('adb -s {0} reboot'.format(self.serial_telefono))

        self.logger.warning('Esperando mientras el telefono se reinicia')
        time.sleep(120)

        self.logger.warning('Iniciando SL4A en el Telefono')
        cmd = '''adb -s {0} shell am start -a com.googlecode.android_scripting.action.LAUNCH_SERVER -n com.googlecode.android_scripting/.activity.ScriptingLayerServiceLauncher --ei com.googlecode.android_scripting.extra.USE_SERVICE_PORT {1}'''.format(self.serial_telefono, self.puerto_telefono)
        os.system(cmd)
        time.sleep(20)

        self.logger.warning('Redirigiendo el Puerto...')
        os.system('adb -s {0} forward tcp:{1} tcp:{2}'.format(self.serial_telefono, self.puerto_adb_forward, self.puerto_telefono))
        time.sleep(10)

    def main(self):
        ''' Main Proncipal'''

        self.sms()

    def run(self):
        ''' Este metodo es el que permite ejecutar el hilo del demonio'''
        
        self.reiniciarTelefono()
        while True:
            #Es necesario volver a conectar cuando se reincia el telefono
            #Colcoar que si no logra a cpnexpn es xq prbablemente debe estarse 
            #reiniciando el telefono, qee espere 2 minutos aprox
            #antes de volver a intentarlo
            
            self.logger.debug("Debug message")
            self.main()
            time.sleep(15)

#Instancio la Clase
app = ubicaText()
handler = app.configLog()
daemon_runner = runner.DaemonRunner(app)

#Esto garantiza que el identificador de archivo logger no quede cerrada durante daemonization
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
