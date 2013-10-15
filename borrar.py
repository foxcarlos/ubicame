#!/usr/bin/env python

import os
import ConfigParser

class test():
    def __ini__(self):
        public nada
        fc  = ConfigParser.ConfigParser()
        fc.read('/home/cgarcia/desarrollo/python/ubicame/ubicame.cfg')

    def verificaSms(self, comando, numero, parametros):
        ''' Verifica si los parametros pasados en el sms
        son correctos'''

        self.parametros = parametros
        self.comando = comando
        self.numero = numero
        listaAutorizados = [auto[1] for auto in fc.items('AUTORIZADOS')]
        param2 = ''
        param3 = ''

        mensaje = self.parametros.split()

        if len(mensaje) == 1:
            comando = mensaje[0]

        elif len(mensaje) == 2:
            comando, param2 = mensaje

        elif len(mensaje) == 3:
            comando, param2, param3 = mensaje

        if numero in listaAutorizados or param3 in listaAutorizados:
            print('Autorizado')


