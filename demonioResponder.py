#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
from daemon import runner
import os
import sys
import ConfigParser
import android

class smsResponder():
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
        del archivo de configuracion pyloro.cfg que se
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

    def gps(self):
        ''' '''
        self.droid.startLocating(3600,1)
        time.sleep(10)
        fin = True
        segundos = 300
        seg_trancurridos = 0
        
        while fin:
            time.sleep(1)
            seg_trancurridos += 1
            l = self.droid.readLocation()
            ll = l.result
            
            if "gps" in ll:
                mensaje = u"Posición actual: "
                pos = (str(ll["gps"]["latitude"]), str(ll["gps"]["longitude"]))
                fin = False
                self.droid.makeToast(u"Posición GPS encontrada")
            else:
                if seg_trancurridos == segundos: 
                    fin = False
                
                    if "network" in ll:
                        pos = (str(ll["network"]["latitude"]), str(ll["network"]["longitude"]))
                        mensaje = u"Posición red celular: "
                        #self.droid.makeToast(u"Posición Red Celular encontrada")
                    else:
                    
                        ll = self.droid.getLastKnownLocation().result
                        pos = (str(ll["network"]["latitude"]), str(ll["network"]["longitude"]))
                        mensaje = u"Ultima posición red celular: "
                        #self.droid.makeToast(u"No se pudo establecer conexión, se enviara la ultima posición registrada")

        pll = "%s,%s" % (str(pos[0]), str(pos[1]))
        mapa = "http://maps.google.com/maps?ll=%s&q=%s" % (pll, pll)
        self.droid.stopLocating()
        return mensaje, mapa    

    def abrir(self, id, numero):
        ''' metodo para envio de señal al selenoide'''
        pass
        self.droid.smsMarkMessageRead([id], True)

    def smsProcesar(self, registros):
        ''' '''

        print(registros)
        for fila in registros:
            id, numero, cuerpo = fila          
            cuerpo =  cuerpo if cuerpo else 'vacio'
            #mensaje = self.responder
            
            if cuerpo.strip().upper() == 'GPS':
                mensaje, mapa = self.gps(id, numero)

            elif cuerpo.strip().upper() == 'ABRIR':
                self.abrir(id, numero)
            
            '''
            #Eliminar espacios que estan demas del mensajes
            separarCuerpo = cuerpo.strip().upper().split(' ')
            contarEspacios = separarCuerpo.count('')
            for veces in range(contarEspacios):
                separarCuerpo.remove('')

            mensaje = ''
            comando = separarCuerpo[0]
            parametro = separarCuerpo[1] if len(separarCuerpo) > 1 else ''
            if len(separarCuerpo) == 1 and ('AYUDA' in separarCuerpo):
                #print('Pidio ayuda')
                mensaje = self.responder  # self.procesarAyuda()
            elif comando == 'CONSULTAR':
                #print('Consultando su Cita segun cedula {0}'.format(parametro))
                mensaje = self.responder  # 'Su cita esta pautada para el dia dd/mm/aaaa'  # self.procesarConsultar(parametro)
            elif comando == 'CONFIRMAR':
                #print('Confirmando su Cita')
                mensaje = self.responder  # 'Confirmada su cita para el dia dd/mm/aaaa'  # self.procesarConfirmar(parametro)
            elif comando == 'CANCELAR':
                #print('Cancelando la Cita dada a la cedula {0}'.format(parametro))
                mensaje = self.responder  # 'Su cita del dia dd/mm/aaaa fue cancelada con exito'  # self.procesarCancelar(parametro)
            elif comando == 'POSPONER':
                #print('Posponiendo su Cita de la cedula {0} para la fecha xx/xx/xxxxx'.format(parametro))
                mensaje = self.responder  # 'Su cita del dia dd/mm/aaaa fue pospuesta para el dia dd/mm/aaaa'  # self.procesarPosponer(parametro)
            elif comando == 'ELIMINAR':
                #print('Eliminando Numero de Telefono de las Notificaciones')
                mensaje = self.responder  # 'Su numero telefonico fue eliminado de la lista de notificaciones'  # self.procesarEliminar(parametro)
            else:
                #print('Ninguna de las Anteriores')
                mensaje =  self.responder  # procesarNingunaAnteriores()
            '''
        return True

    def smsRecibidos(self):
        ''' Metodo que permite buscar los SMS enviados por los
         en bandeja de entrada pacientes y guardarlos en una lista 
         para luego ser procesados con el Metodo enviarSocket()
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

    def conectarAndroid(self):
        ''' Metodo que permite recorrer el archivo de configuracion .cfg
        y buscar los telefonos Android conectados via usb para instanciarlos
        para poder obtener los sms en bandeja de entrada'''

        os.system('adb -s {0} wait-for-device'.format(self.serial_telefono))
        try:
            self.droid = android.Android((self.ip_telefono, self.puerto_adb_forward))
            #print('Conectando el telefono {0}, {1}'.format(ip_telefono, puerto_adb_forward))
            smsListaR = self.smsRecibidos()

            smsListaP = self.smsProcesar(smsListaR)
            
            #self.enviarSocket(smsListaP)
            time.sleep(10)
        except:
            self.logger.error('No se pudo Conectar con el Telefono Servidor Android')    
            self.logger.warning('Redirigiendo el Puerto debido a un error al momento de intentar conectar el telefono Android')
            os.system('adb -s {0} forward tcp:{1} tcp:{2}'.format(self.serial_telefono, self.puerto_adb_forward, self.puerto_telefono))
            time.sleep(10)

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
        ''' '''
        self.logger.info('Proceso iniciado <Contestar al Paciente>')      
        self.conectarAndroid()
        self.logger.info('Proceso Finalizado <Contestar al Paciente>')

    def run(self):
        ''' Este metodo es el que permite ejecutar el hilo del demonio'''
        
        self.reiniciarTelefono()
        while True:
            #Es necesario volver a conectar cuando se reincia el telefono
            #Colcoar que si no logra a cpnexpn es xq prbablemente debe estarse reiniiando el telefpmnp, qie espere 2 minutos aprox
            #antes de volver a intentarlo
            
            self.logger.debug("Debug message")
            self.main()
            time.sleep(30)

#Instancio la Clase
app = smsResponder()
handler = app.configLog()
daemon_runner = runner.DaemonRunner(app)

#Esto garantiza que el identificador de archivo logger no quede cerrada durante daemonization
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()