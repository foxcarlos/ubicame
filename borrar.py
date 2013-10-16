#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ConfigParser

class test():
    def __init__(self):
        self.fc  = ConfigParser.ConfigParser()
        self.fc.read('/home/cgarcia/desarrollo/python/ubicame/ubicame.cfg')

    def verificaSms(self, numero, parametros):
        ''' Verifica si los parametros pasados en el sms
        son correctos'''

        self.parametros = parametros
        mensaje = self.parametros.split()
        self.numero = numero
        listaAutorizados = [auto[1] for auto in self.fc.items('AUTORIZADOS')]
        param2 = ''
        param3 = mensaje[2] if len(mensaje) == 3 else ''
        comandoDevolver = ''

        #Verifica si el numero telefonico esta autorizado para enviar comandos
        if numero in listaAutorizados or param3 in listaAutorizados:
            if len(mensaje) == 1:
                comando = mensaje[0].lower()
                if self.fc.has_option('EVENTOS', comando):
                    if self.fc.get('EVENTOS', comando):
                        self.error, comandoDevolver = True, 'El Comando:{0} necesita un paremetro adicional,\
                        Ej: LUCES ON'.format(comando)
                else:
                    self.error, comandoDevolver = True, 'El Comando:{0} no Existe, escriba un comando valido'.format(comando)
            elif len(mensaje) == 2:
                comando, param2 = mensaje
                if self.fc.has_option('EVENTOS', comando):
                    valorEventos = self.fc.get('EVENTOS', comando).split(',')
                    if param2.lower() in valorEventos:
                        self.error, comandoDevolver = False, self.parametros
                    else:
                        self.error, comandoDevolver = True, 'El Comando:{0} no contiene el Parametro:{1}'.format(
                            comando, param2)
                else:
                    self.error, comandoDevolver = True, 'El Comando:{0} no Existe, escriba un comando valido'.format(comando)
            elif len(mensaje) == 3:
                comando, param2, param3 = mensaje
                if self.fc.has_option('EVENTOS', comando):
                    valorEventos = self.fc.get('EVENTOS', comando).split(',')
                    if param2.lower() in valorEventos:
                        self.error, comandoDevolver = False, comando + ' ' + param2
                    else:
                        self.error, comandoDevolver = True, 'El Comando:{0} no contiene el Parametro:{1}'.format(
                            comando, param2)
                else:
                    self.error, comandoDevolver = True, 'El Comando:{0} no Existe, escriba un comando valido'.format(comando)
        else:
            self.error, comandoDevolver = True, 'Telefono no esta Autotizado o Contraseña Invalida'
        return self.error, comandoDevolver

if __name__ == '__main__':
    app = test()
    para = 'gps on carlos'
    x = app.verificaSms('0463002966', para)
    print(x)
