 #!/usr/bin/env python
# -*- coding: utf-8 -*-
# encoding: utf-8

from tkinter import *
import tkinter as tk
import time
from random import randint
import threading
import os
from datetime import datetime
import cognitive_face as CF
import requests
import json
import sqlite3
import io
from multiprocessing import Process
import ftplib

import RPi.GPIO as GPIO
from mfrc522_2 import SimpleMFRC522_2
from mfrc522 import SimpleMFRC522

RFid_1 = SimpleMFRC522()
RFid_2 = SimpleMFRC522_2()

conexaoBanco=sqlite3.connect('matematica.db')
banco=conexaoBanco.cursor()

conexaoBancoAjuste=sqlite3.connect('ajuste.db')
bancoAjuste=conexaoBancoAjuste.cursor()
sqlUp="UPDATE tabAjuste SET valor=" + str(-1) + " where id=1"
bancoAjuste.execute(sqlUp)
conexaoBancoAjuste.commit()
conexaoBancoAjuste.close()

contador=0
botaoVerde=40
botaoAzul=38
botaoAmarelo=36
botaoVermelho=32
GPIO.setmode(GPIO.BOARD)
 
#Define o pino do botao como entrada
GPIO.setup(botaoVerde, GPIO.IN)
GPIO.setup(botaoAzul, GPIO.IN)
GPIO.setup(botaoAmarelo, GPIO.IN)
GPIO.setup(botaoVermelho, GPIO.IN)

# API MS Face
KEY = 'd6341b3f7130422f8f4502fd6ec4b85b'  # Chave da API .
CF.Key.set(KEY)
BASE_URL = 'https://brazilsouth.api.cognitive.microsoft.com/face/v1.0/'  # URL Regional
CF.BaseUrl.set(BASE_URL)
img_url=None


ResultadoEsperado=0
RespUsuarioDez=0
RespUsuarioUni=0
RespUsuarioTot=0
N1=0
N2=0
nivel=0
operacao=None
codigoUsuario=None
sorteioEstado=None
momento=None
cicloAtual=None
arquivo=None
precisaInverter=None



felicidade=-1
raiva=-1
neutro=-1
surpreso=-1
tristeza=-1
desprezo=-1
medo=-1
desgosto=-1
genero=-1
idade=-1


# print("quantidade de Cartões cadastrados = " +str(tamanhoCadCartao))

############################
#### Funções
estadoBotaoVerde=0
estadoBotaoAzul=0
estadoBotaoAmarelo=0
estadoBotaoVermelho=0

tela='inicial'
telaEstado='nada'

def desligaSistema():
    data_e_hora_atuais = datetime.now()
    data_e_hora_em_texto = data_e_hora_atuais.strftime('%y-%m-%d')
    comando="sqlite3 matematica.db .dump > matematica_Dump_"+data_e_hora_em_texto+".sql"
    os.system (comando) # BACKUP do BANCO DE DADOS
    
    arquivoFTP="matematica_Dump_"+data_e_hora_em_texto+".sql"
    
    # Mandando O Bak do Banco para um ftp 
    processo_FTP = Process(target=mandaFTP(arquivoFTP)) # Criando um processo 
    processo_FTP.start() # Iniciando
    processo_FTP.join(timeout=30) # esperando este tempo em segundos
    processo_FTP.terminate() # Encerrando o processo
    print("Desligando . . . . .")
    time.sleep(1)
    os.system('sudo shutdown -h now') # Desliga o SISTEMA
    
def sairSistema():
    print("Back Banco . . . . .")
    data_e_hora_atuais = datetime.now()
    data_e_hora_em_texto = data_e_hora_atuais.strftime('%y-%m-%d')
    comando="sqlite3 matematica.db .dump > matematica_Dump_"+data_e_hora_em_texto+".sql"
    os.system (comando) # BACKUP do BANCO DE DADOS
    
    arquivoFTP="matematica_Dump_"+data_e_hora_em_texto+".sql"
    
    # Mandando O Bak do Banco para um ftp 
    processo_FTP = Process(target=mandaFTP(arquivoFTP)) # Criando um processo 
    processo_FTP.start() # Iniciando
    processo_FTP.join(timeout=30) # esperando este tempo em segundos
    processo_FTP.terminate() # Encerrando o processo
    print(". . . . . . . . . . . . . . . . . . . . . ")
    time.sleep(1)
    os._exit(0)
    #os.system('sudo shutdown -h now') # Desliga o SISTEMA    
# código do cartão , número associado

cadCartao=[[666127655853 , 0],[368600507305 , 0],
           [1009695050677 , 1],[1009287572992 , 1],
           [733469072286 , 2],[7927483281 , 2],
           [1075072295835 , 3],[789963852562 , 3],
           [488473715684 , 4],[469300923233 , 4],
           [606014890938 , 5],[863599053715 , 5],
           [444604861355 , 6],[682200163175 , 6],
           [1008705194873 , 7],[109637773789 , 7],
           [420193946621 , 8],[30388544315 , 8],
           [953978891258 , 9],[991783725391 , 9]]

tamanhoCadCartao=len(cadCartao)

def pesquisa(cartao):
    for index in range(tamanhoCadCartao):
        if (cadCartao[index][0]== cartao):
            return index
    return -1;  


def lerCartao_Dez():
    global RespUsuarioDez
    valor_Dez,texto_lixo = RFid_2.read()
    index=pesquisa(valor_Dez) # faz a pesquisa na matriz de cartões
    if (index>=0):
        RespUsuarioDez=cadCartao[index][1]
        RespUsuarioDez=RespUsuarioDez*10 #Multiplicando por 10
    print("Leitor Dezena Codigo = " +str(valor_Dez) +"  || Valor Dezena = " +str(RespUsuarioDez))

def lerCartao_Uni():
    global RespUsuarioUni
    valor_Uni,texto_lixo = RFid_1.read()

    index=pesquisa(valor_Uni) # faz a pesquisa na matriz de cartões
    if (index>=0):
        RespUsuarioUni=cadCartao[index][1]

    print("Leitor Unidade Codigo = " +str(valor_Uni) +"  || Valor Unidade = " +str(RespUsuarioUni))
 

   
def sorteioNumeros():
    global ResultadoEsperado
    global N1
    global N2
    global operacao
    global nivel

    global precisaInverter
    global jaInverteu
    ##############
    conexaoBancoAjuste=sqlite3.connect('ajuste.db')
    bancoAjuste=conexaoBancoAjuste.cursor()
    for linha in bancoAjuste.execute("SELECT valor FROM tabAjuste WHERE id=1;"):
        ajuste=int(linha[0])
    conexaoBancoAjuste.close()
    ##################
    if (precisaInverter=='S' and jaInverteu==None ):
        X=N1
        N1=N2
        N2=X
        precisaInverter='N'
        jaInverteu='S'
    else:   
        if (nivel==21):
            if (operacao=='+'):
                if(ajuste>=5):
                    N1 = randint(1,8)
                    N2 = randint(0,abs(N1-9))
                elif (ajuste>=3 and ajuste <5):
                    N1 = randint(1,6)
                    N2 = randint(1,abs(N1-9))
                else:
                    N1 = randint(1,3)
                    N2 = randint(1,3)
                
            ResultadoEsperado=N1+N2
            
        if (operacao=='-'):
            if(ajuste>=5):
                N1 = randint(4,9)
                N2 = randint(0,N1)
            elif (ajuste>=3 and ajuste <5):
                N1 = randint(2,8)
                N2 = randint(1,N1)
            else:
                N1 = randint(2,5)
                N2 = randint(1,N1)
                    
            ResultadoEsperado=N1-N2 
        
        if (operacao=='x'):
            if(ajuste>=5):
                N1 = randint(1,5)
                N2 = randint(0,10)
            elif (ajuste>=3 and ajuste <5):
                N1 = randint(1,3)
                N2 = randint(1,10)
            else:
                N1 = randint(1,2)
                N2 = randint(0,5)
            
            ResultadoEsperado=N1*N2


    if (nivel==22):
        if (operacao=='+'):
            if(ajuste>=5):
                N1 = randint(10,20)
                N2 = randint(5,20)
            elif (ajuste>=3 and ajuste <5):
                N1 = randint(5,10)
                N2 = randint(5,10)
            else:
                N1 = randint(5,10)
                N2 = randint(1,5)
            
            ResultadoEsperado=N1+N2
            
        if (operacao=='-'):
            if(ajuste>=5):
                N1 = randint(4,9)
                N2 = randint(0,N1)
            elif (ajuste>=3 and ajuste <5):
                N1 = randint(6,9)
                N2 = randint(1,N1)
            else:
                N1 = randint(2,5)
                N2 = randint(1,N1)
                    
            ResultadoEsperado=N1-N2 
        
        if (operacao=='x'):
            if(ajuste>=5):
                N1 = randint(2,10)
                N2 = randint(0,10)
                if(N1==10 and N2==10):
                    N2=9
            elif (ajuste>=3 and ajuste <5):
                N1 = randint(3,6)
                N2 = randint(1,10)
            else:
                N1 = randint(1,3)
                N2 = randint(1,10)
            
            ResultadoEsperado=N1*N2
        
    if (nivel==31):
        if (operacao=='+'):
            if(ajuste>=5):
                N1 = randint(1,99)
                N2 = randint(0,abs(N1-99))
            elif (ajuste>=3 and ajuste <5):
                N1 = randint(1,50)
                N2 = randint(0,abs(N1-60))
            else:
                N1 = randint(1,30)
                N2 = randint(0,abs(N1-50))
            
            ResultadoEsperado=N1+N2
            
        if (operacao=='-'):
            if(ajuste>=5):
                N1 = randint(50,99)
                N2 = randint(10,N1)
            elif (ajuste>=3 and ajuste <5):
                N1 = randint(30,80)
                N2 = randint(10,30)
            else:
                N1 = randint(20,50)
                N2 = randint(1,20)
                    
            ResultadoEsperado=N1-N2 
        
        if (operacao=='x'):
            if(ajuste>=5):
                N1 = randint(2,10)
                N2 = randint(0,10)
                if(N1==10 and N2==10):
                    N2=9
            elif (ajuste>=3 and ajuste <5):
                N1 = randint(3,7)
                N2 = randint(1,10)
            else:
                N1 = randint(1,5)
                N2 = randint(1,10)
            
            ResultadoEsperado=N1*N2

    
    print(" @@@@@@@ N1 = " +str(N1) +"  @@@@@@@ N2 = "+str(N2) +"   Resultado esperado = " + str(ResultadoEsperado))

    exibeTela = str(N1) +" "+operacao+" " +str(N2) +" = ___"

    txtMeio =exibeTela
    lblMeio=Label(janela,text=txtMeio,font=("Arial",60,'bold'),fg = corTexto, bg=corFundo, width=25, height=3)
    lblMeio.place(relx=.4, rely=.4, anchor="center")

    janela.update()
    foto('Pre')

 
def foto(momentoRecebe):
    conexaoBanco=sqlite3.connect('matematica.db')
    banco=conexaoBanco.cursor()
    global cicloAtual
    global momento
    global N1
    global N2
    global codigoUsuario
    global operacao
    global nivel
    global RespUsuarioUni
    global RespUsuarioDez
    global RespUsuarioTot
    global ResultadoEsperado
    global arquivo
    global felicidade
    global raiva
    global neutro
    global surpreso
    global tristeza
    global desprezo
    global medo
    global desgosto
    global genero
    global idade
    
    felicidade=-1
    raiva=-1
    neutro=-1
    surpreso=-1
    tristeza=-1
    desprezo=-1
    medo=-1
    desgosto=-1
    genero=-1
    idade=-1
    global momento
    global codigoUsuario
 
    data_e_hora_atuais = datetime.now()
    data_e_hora_em_texto = data_e_hora_atuais.strftime('%y%m%d-%H-%M-%S')
    arquivo='capturas/IMG_'+data_e_hora_em_texto+'_U'+str(codigoUsuario)+'_M'+str(momentoRecebe)+'.jpg'
    comando="fswebcam -r640x480 "+arquivo #comando para a captura juntamente com data e Hora + usuário +momento
    os.system (comando) #executa

    # Mandando para a API 
    processo_API = Process(target=recebeEmocao) # Criando um processo para a API
    processo_API.start() # Iniciando
    processo_API.join(timeout=10) # esperando este tempo em segundos
    processo_API.terminate() # Encerrando o processo
    
    ### buscando ajuste
    conexaoBancoAjuste=sqlite3.connect('ajuste.db')
    bancoAjuste=conexaoBancoAjuste.cursor()
    for linha in bancoAjuste.execute("SELECT valor FROM tabAjuste WHERE id=1;"):
        ajuste=int(linha[0])
    conexaoBancoAjuste.close()
    ###
    print("Gravando no banco de Dados matematica. . .")
    banco.execute ("INSERT INTO tabDados(data, hora, codAluno, nomeIMG, nivel, tipoOperacao, N1 , N2, respostaUsuario, ajuste ,ciclo , momento, apiNeutro , apiFelicidade , apiSurpreso , apiRaiva , apiTristeza , apiDesprezo , apiDesgosto  ,apiMedo , apiIdade , apiGenero ) values(date('now'), time('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)" , (codigoUsuario, arquivo, nivel, operacao, N1 , N2, RespUsuarioTot, ajuste ,cicloAtual ,momento, neutro , felicidade , surpreso , raiva , tristeza , desprezo , desgosto  ,medo , idade , genero ))
    conexaoBanco.commit()
    conexaoBanco.close()
    
    thread_FTP = threading.Thread(target=mandaFTP,args=(arquivo,))
    thread_FTP.start()
    
def mandaFTP(caminhoLocal):
    #host = "192.168.0.30"
    #username = "rasp"
    #password = "123"
    host = "ftp.vansan.com.br"
    username = "MatematicaEmocao@vansan.com.br"
    password = "s8Nu#ORyv.V?WD3PUw"
 
    try:
        caminhoRemoto='STOR '+caminhoLocal
            
        print("Enviando para o FTP = " +caminhoLocal)   
        session = ftplib.FTP(host,username,password)
        file = open(caminhoLocal,'rb') # file to send
        session.storbinary(caminhoRemoto, file) # send the file
        file.close()    # close file and FTP
        session.quit()
        print("FTP OK = " +caminhoLocal)
    except:
        print("\n Erro no envio para o FTP= " +caminhoLocal)    
    
    
def recebeEmocao():
    global cicloAtual
    global momento
    global N1
    global N2
    global codigoUsuario
    global operacao
    global nivel
    global RespUsuarioUni
    global RespUsuarioDez
    global RespUsuarioTot
    global ResultadoEsperado
    global arquivo
    global felicidade
    global raiva
    global neutro
    global surpreso
    global tristeza
    global desprezo
    global medo
    global desgosto
    global genero
    global idade
    global corFundo
    global corTexto
    global textoErrado
    global textoCerto
    
    ###
    try:
        img_url=arquivo
        attributes = ('age,gender,emotion')
        print("enviando o arquivo para API " +arquivo)
        resultadoEmocao = json.dumps(CF.face.detect(img_url, False, False, attributes))
        resultadoEmocao = json.loads(str(resultadoEmocao))[0]
        #print("tipo dado" +str(type(resultadoEmocao)))
        felicidade=resultadoEmocao['faceAttributes']['emotion']['happiness']
        raiva=resultadoEmocao['faceAttributes']['emotion']['anger']
        neutro=resultadoEmocao['faceAttributes']['emotion']['neutral']
        surpreso=resultadoEmocao['faceAttributes']['emotion']['surprise']
        tristeza= resultadoEmocao['faceAttributes']['emotion']['sadness']
        desprezo= resultadoEmocao['faceAttributes']['emotion']['contempt']
        medo= resultadoEmocao['faceAttributes']['emotion']['fear']
        desgosto= resultadoEmocao['faceAttributes']['emotion']['disgust']
        genero=resultadoEmocao['faceAttributes']['gender']
        idade=resultadoEmocao['faceAttributes']['age']
        
        conexaoBancoAjuste=sqlite3.connect('ajuste.db')
        bancoAjuste=conexaoBancoAjuste.cursor()
        
        for linha in bancoAjuste.execute("SELECT valor FROM tabAjuste WHERE id=1;"):
            varRecebeAjuste=int(linha[0])
        
        print('Ajuste= '+str(varRecebeAjuste) +' || CicloAtual = ' +str(cicloAtual) + ' || Erros = ' + str(erros) + ' || Acertos = ' +str(acertos))
        if (felicidade >=0.1 or surpreso >=0.2):
            if (varRecebeAjuste<10):
                varRecebeAjuste=varRecebeAjuste+1
                print('Feliz ou Surpreso para +1 . . . ' +str(varRecebeAjuste))
            else:
                varRecebeAjuste=10
                print('Feliz ou Surpreso Max  =10 . . . ' +str(varRecebeAjuste))   
        
        if (neutro>= 0.7):
            if (varRecebeAjuste>=1):
                varRecebeAjuste=varRecebeAjuste-1
                print('Neutro para -1. . . ' +str(varRecebeAjuste))
            else:
                varRecebeAjuste=1
                print('Neutro Min para 1 . . . ' +str(varRecebeAjuste))
        
        if (tristeza>= 0.1 or raiva>=0.1):
            if (varRecebeAjuste>=2):
                varRecebeAjuste=varRecebeAjuste-2
                print('Triste ou Raiva para -2. . . ' +str(varRecebeAjuste))
            else:
                varRecebeAjuste=0
                print('Triste ou Raiva Max = 0 . . . ' +str(varRecebeAjuste))
                
        sqlUp="UPDATE tabAjuste SET valor=" + str(varRecebeAjuste) + " where id=1"
        bancoAjuste.execute(sqlUp)
        conexaoBancoAjuste.commit()
        conexaoBancoAjuste.close()
        ###        
        print('Neutro= '+ str(resultadoEmocao['faceAttributes']['emotion']['neutral']))
        print('Felicidade= '+ str(resultadoEmocao['faceAttributes']['emotion']['happiness']))
        print('Surpreso= '+ str(resultadoEmocao['faceAttributes']['emotion']['surprise']))
        print('Raiva= '+ str(resultadoEmocao['faceAttributes']['emotion']['anger']))        
        print('Tristeza= '+ str(resultadoEmocao['faceAttributes']['emotion']['sadness']))
        print('Desprezo= '+ str(resultadoEmocao['faceAttributes']['emotion']['contempt']))
        print('Medo= '+ str(resultadoEmocao['faceAttributes']['emotion']['fear']))
        print('Desgosto= '+ str(resultadoEmocao['faceAttributes']['emotion']['disgust']))

        print('\nGenero= '+ str(resultadoEmocao['faceAttributes']['gender']))
        print('Idade= '+ str(resultadoEmocao['faceAttributes']['age']))
       # sugestao=(neutro+felicidade+surpreso)-(raiva+tristeza+desprezo+desgosto+medo) 
       # print('###### SUGESTAO Ajuste = '+ str(sugestao))  
       # print('\n###### Ajuste Atual= '+ str(varRecebeAjuste))
       

    #   print("\n Exibindo dados do dicionario ")
    #   for dado in resultadoEmocao:
    #       print("%s: %s \n" % (dado, resultadoEmocao[dado]))
    
       
        
    
    except:
        print("\n Erro no processamento da imagem ")

 

def MicroControlador(mensagem):
    global tela
    global estadoBotaoVerde
    global estadoBotaoAzul
    global estadoBotaoAmarelo
    global estadoBotaoVermelho
    
    print("Rodando Micro Controlador")
    while(True):
        time.sleep(0.1)
        #Verifica se o botao foi pressionado
        if GPIO.input(botaoVerde) == True:
            print("Botão VERDE Pressionado >>>")
            estadoBotaoVerde=1
            time.sleep(1)
        else:
            estadoBotaoVerde=0  
        if GPIO.input(botaoAzul) == True:
            print("Botão AZUL Pressionado >>>")
            estadoBotaoAzul=1
            time.sleep(1)
        else:
            estadoBotaoAzul=0
        if GPIO.input(botaoAmarelo) == True:
            print("Botão AMARELO Pressionado >>>")
            estadoBotaoAmarelo=1
            time.sleep(1)
        else:
            estadoBotaoAmarelo=0
        if GPIO.input(botaoVermelho) == True:
            print("Botão VERMELHO Pressionado >>>")
            estadoBotaoVermelho=1
            time.sleep(1)
        else:
            estadoBotaoVermelho=0
            
            
        if ((GPIO.input(botaoVermelho) == True) and (GPIO.input(botaoAmarelo) == True)):
            if((GPIO.input(botaoAzul) == True) and (GPIO.input(botaoVerde) == True)):
                desligaSistema() # DESLIGA o SISTEMA

        if (GPIO.input(botaoVermelho) == True and GPIO.input(botaoAmarelo) == True and GPIO.input(botaoVerde) == True):
            os.system('sudo shutdown -r now') # REINICIA o SISTEMA
        
 
 
def gerenciador_de_Telas(mensagem):
    global ajuste
    global cicloAtual
    global N1
    global N2
    global sorteioEstado
    global codigoUsuario
    global operacao
    global nivel
    global tela
    global telaEstado
    global estadoBotaoVerde
    global estadoBotaoAzul
    global estadoBotaoAmarelo
    global estadoBotaoVermelho
    global RespUsuarioUni
    global RespUsuarioDez
    global RespUsuarioTot
    global ResultadoEsperado
    global precisaInverter
    global jaInverteu
    global corFundo
    global corTexto
    global textoErrado
    global textoCerto
    global acertos
    global erros
    
    corTextoPadrao='#0000CD'
    corFundoPadrao='#FAE566'
    corFundo='#D3D3D3'
    corTexto='#1C1C1C'
    textoErrado='textoErrado'
    textoCerto='textoCerto'
    
    print("Rodando Gerenciador de Telas")
    while(True):
        time.sleep(0.5)
        #print("Tela = " + tela + "  || Estado tela =" + telaEstado)
        # print("Verde = "+ str(estadoBotaoVerde) + " || Azul = " + str(estadoBotaoAzul) + " || Amarelo = " + str(estadoBotaoAmarelo) + " || Vermelho = " + str(estadoBotaoVermelho))
        ########## Montando as telas
        #### Consulta Banco para alterar cores
        conexaoBancoAjuste=sqlite3.connect('ajuste.db')
        bancoAjuste=conexaoBancoAjuste.cursor()
        for linha in bancoAjuste.execute("SELECT valor FROM tabAjuste WHERE id=1;"):
            varRecebeAjuste=int(linha[0])
        conexaoBancoAjuste.close()
        
        ### Debug
        #txtAjuste = (">>>>>  Ajuste no Banco = " +str(varRecebeAjuste))
        #lblAjuste=Label(janela,text=txtAjuste,font=("Arial",30,'bold'),fg = '#ffffff', bg='#000000', width=25, height=2)
        #lblAjuste.place(relx=.3, rely=.6, anchor="center")
        
        
        if (varRecebeAjuste<=10):
            corFundo='#8FEB78'
            corTexto='#363636'
            textoErrado='Que pena,está errado \nnão foi dessa vez.'
            textoCerto='Parabéns Você Acertou !'             
        if (varRecebeAjuste<=7):
            corFundo='#8DEBDB'
            corTexto='#363636'
            textoErrado='Que pena,está errado \nvamos tentar novamente?'
            textoCerto='Muito bom, está correto!'           
        if (varRecebeAjuste<=5):
            corFundo='#DCDCDC'
            corTexto='#363636'
            textoErrado='Que pena,está errado \nda próxima vez dará certo!'
            textoCerto='Parabéns Você Acertou!\nContinue assim!'             
        if (varRecebeAjuste<=4):
            corFundo='#EB9138'
            corTexto='#363636'
            textoErrado='Que pena,está errado \ncontinue tentando'
            textoCerto='Muito bom, está correto!\nVamos que vamos!'         
        if (varRecebeAjuste<=2):
            corFundo='#EBDA8B'
            corTexto='#363636'
            textoErrado='Que pena,está errado \nVocê consegue!'
            textoCerto='Parabéns Você Acertou! \nContinue assim!'  

      ### mudar cor e texto conforme ajuste
       ### Tela Inicial
        if (tela=='inicial' and telaEstado!='inicial'):
            telaEstado='inicial'
            #print(" >>>>> Tela Inicial Mesmo")

            txtCima="Matemática "
            lblCima=Label(janela,text=txtCima,font=("Arial",30,'bold'),fg = corTextoPadrao , bg=corFundoPadrao, width=30, height=3)
            lblCima.place(relx=.4, rely=.1, anchor="center")

            txtMeio = "Seja bem Vindo(a)"  
            lblMeio=Label(janela,text=txtMeio,font=("Arial",60,'bold'),fg = corTextoPadrao, bg=corFundoPadrao, width=25, height=3)
            lblMeio.place(relx=.4, rely=.4, anchor="center")

            txtBaixo = "Pressione o botão \nVERDE para continuar"
            lblBaixo=Label(janela,text=txtBaixo,font=("Arial",30,'bold'),fg = "green", bg=corFundoPadrao, width=30, height=3)
            lblBaixo.place(relx=.4, rely=.8, anchor="center")

            txtVermelho = "DESLIGAR"
            lblVermelho=Label(janela,text=txtVermelho,font=("Arial",30,'bold'),fg = "red", width=10, height=3)
            lblVermelho.place(relx=.9, rely=.2, anchor="center")
            lblVermelho['text']=txtVermelho

            txtAmarelo = " "
            lblAmarelo=Label(janela,text=txtAmarelo,font=("Arial",30,'bold'),fg = "yellow", width=10, height=3)
            lblAmarelo.place(relx=.9, rely=.4, anchor="center")

            txtAzul = "Calibrar\nWebcam "
            lblAzul=Label(janela,text=txtAzul,font=("Arial",30,'bold'),fg = "blue", width=10, height=3)
            lblAzul.place(relx=.9, rely=.6, anchor="center")

            txtVerde = "Continuar"
            lblVerde=Label(janela,text=txtVerde,font=("Arial",30,'bold'),fg = "green", width=10, height=3)
            lblVerde.place(relx=.9, rely=.8, anchor="center")
            
            time.sleep(1)
            
        ### Tela Desligar       
        if (tela=='desligar' and telaEstado!='desligar'):
            #print(" >>>>> Tela Desligar Mesmo")
            telaEstado='desligar'
            
            txtCima="Confirma?"
            janela.lblCima=Label(janela,text=txtCima,font=("Arial",30,'bold'),fg = corTextoPadrao, bg=corFundoPadrao, width=30, height=3 )
            janela.lblCima.place(relx=.4, rely=.1, anchor="center")
            lblCima['text']=txtCima

            txtMeio = "Pressione Verde \npara desligar"  
            lblMeio=Label(janela,text=txtMeio,font=("Arial",60,'bold'),fg = "green", bg=corFundoPadrao, width=25, height=3)
            lblMeio.place(relx=.4, rely=.4, anchor="center")
            lblMeio['text']=txtMeio

            txtBaixo = "Pressione Vermelho\npara Voltar"
            lblBaixo=Label(janela,text=txtBaixo,font=("Arial",30,'bold'),fg = "red", bg=corFundoPadrao, width=30, height=3)
            lblBaixo.place(relx=.4, rely=.8, anchor="center")
            lblBaixo['text']=txtBaixo

            txtVermelho = "Voltar"
            #lblVermelho=Label(janela,text=txtVermelho,font=("Arial",30,'bold'),fg = "red", width=10, height=3)
            #lblVermelho.place(relx=.9, rely=.2, anchor="center")
            lblVermelho['text']=txtVermelho

            txtAmarelo = " "
            #lblAmarelo=Label(janela,text=txtAmarelo,font=("Arial",30,'bold'),fg = "yellow", width=10, height=3)
            #lblAmarelo.place(relx=.9, rely=.4, anchor="center")
            lblAmarelo['text']=txtAmarelo
            
            txtAzul = " "
            #lblAzul=Label(janela,text=txtAzul,font=("Arial",30,'bold'),fg = "blue", width=10, height=3)
            #lblAzul.place(relx=.9, rely=.6, anchor="center")
            lblAzul['text']=txtAzul
            
            txtVerde = "DESLIGAR"
            #lblVerde=Label(janela,text=txtVerde,font=("Arial",30,'bold'),fg = "green", width=10, height=3)
            #lblVerde.place(relx=.9, rely=.8, anchor="center")  
            lblVerde['text']=txtVerde
            janela.update()
            time.sleep(1)
            
        ### Tela Escolher o Nivel   
        if (tela=='nivel' and telaEstado!='nivel'):
            telaEstado='nivel'
            txtCima="Nível ?"
            janela.lblCima=Label(janela,text=txtCima,font=("Arial",30,'bold'),fg = corTextoPadrao, bg=corFundoPadrao, width=30, height=3 )
            janela.lblCima.place(relx=.4, rely=.1, anchor="center")
            lblCima['text']=txtCima

            txtMeio = "Escolha o nível \nde dificuldade"  
            lblMeio=Label(janela,text=txtMeio,font=("Arial",60,'bold'),fg = corTextoPadrao, bg=corFundoPadrao, width=25, height=3)
            lblMeio.place(relx=.4, rely=.4, anchor="center")
            lblMeio['text']=txtMeio

            txtBaixo = "Pressione Vermelho\npara Voltar"
            lblBaixo=Label(janela,text=txtBaixo,font=("Arial",30,'bold'),fg = "red", bg=corFundoPadrao, width=30, height=3)
            lblBaixo.place(relx=.4, rely=.8, anchor="center")
            lblBaixo['text']=txtBaixo

            txtVermelho = "Voltar"
            #lblVermelho=Label(janela,text=txtVermelho,font=("Arial",30,'bold'),fg = "red", width=10, height=3)
            #lblVermelho.place(relx=.9, rely=.2, anchor="center")
            lblVermelho['text']=txtVermelho

            txtAmarelo = "3º Ano\nNível 1 "
            lblAmarelo=Label(janela,text=txtAmarelo,font=("Arial",30,'bold'),fg = "#DAA520", width=10, height=3)
            lblAmarelo.place(relx=.9, rely=.4, anchor="center")
            lblAmarelo['text']=txtAmarelo
            
            txtAzul = "2º Ano\nNível 2"
            #lblAzul=Label(janela,text=txtAzul,font=("Arial",30,'bold'),fg = "blue", width=10, height=3)
            #lblAzul.place(relx=.9, rely=.6, anchor="center")
            lblAzul['text']=txtAzul
            
            txtVerde = "2º Ano\nNível 1"
            #lblVerde=Label(janela,text=txtVerde,font=("Arial",30,'bold'),fg = "green", width=10, height=3)
            #lblVerde.place(relx=.9, rely=.8, anchor="center")  
            lblVerde['text']=txtVerde
            janela.update()
            time.sleep(1)
            
        ### Tela Escolher a operação    
        if (tela=='operacao' and telaEstado!='operacao'):
            telaEstado='operacao'
            
            txtCima="Escolha agora o \nTipo de Operação."
            janela.lblCima=Label(janela,text=txtCima,font=("Arial",30,'bold'),fg = corTextoPadrao, bg=corFundoPadrao, width=30, height=3 )
            janela.lblCima.place(relx=.4, rely=.1, anchor="center")
            lblCima['text']=txtCima

            txtMeio = "Soma, Subtração\nou Multiplicação"  
            lblMeio=Label(janela,text=txtMeio,font=("Arial",60,'bold'),fg = corTextoPadrao, bg=corFundoPadrao, width=25, height=3)
            lblMeio.place(relx=.4, rely=.4, anchor="center")
            lblMeio['text']=txtMeio

            txtBaixo = "Pressione Vermelho\npara Voltar"
            lblBaixo=Label(janela,text=txtBaixo,font=("Arial",30,'bold'),fg = "red", bg=corFundoPadrao, width=19, height=2)
            lblBaixo.place(relx=.4, rely=.8, anchor="center")
            lblBaixo['text']=txtBaixo

            txtVermelho = "Voltar"
            #lblVermelho=Label(janela,text=txtVermelho,font=("Arial",30,'bold'),fg = "red", width=10, height=3)
            #lblVermelho.place(relx=.9, rely=.2, anchor="center")
            lblVermelho['text']=txtVermelho

            txtAmarelo = "Soma\n+ "
            #lblAmarelo=Label(janela,text=txtAmarelo,font=("Arial",30,'bold'),fg = "yellow", width=10, height=3)
            #lblAmarelo.place(relx=.9, rely=.4, anchor="center")
            lblAmarelo['text']=txtAmarelo
            
            txtAzul = "Subtração\n-"
            #lblAzul=Label(janela,text=txtAzul,font=("Arial",30,'bold'),fg = "blue", width=10, height=3)
            #lblAzul.place(relx=.9, rely=.6, anchor="center")
            lblAzul['text']=txtAzul
            
            txtVerde = "Multiplicação\nx"
            #lblVerde=Label(janela,text=txtVerde,font=("Arial",30,'bold'),fg = "green", width=10, height=3)
            #lblVerde.place(relx=.9, rely=.8, anchor="center")  
            lblVerde['text']=txtVerde
            janela.update()
            time.sleep(1)   
        
        ### Tela Código aluno   
        if (tela=='codigo' and telaEstado!='codigo'):
            telaEstado='codigo'
            
            txtCima="Identificação"
            janela.lblCima=Label(janela,text=txtCima,font=("Arial",30,'bold'),fg = corTextoPadrao, bg=corFundoPadrao, width=30, height=3 )
            janela.lblCima.place(relx=.4, rely=.1, anchor="center")
            lblCima['text']=txtCima

            txtMeio = "Coloque seu número \nNo local das respostas"  
            lblMeio=Label(janela,text=txtMeio,font=("Arial",60,'bold'),fg = corTextoPadrao, bg=corFundoPadrao, width=25, height=3)
            lblMeio.place(relx=.4, rely=.4, anchor="center")
            lblMeio['text']=txtMeio

            txtBaixo = "Pressione Verde\npara continuar"
            lblBaixo=Label(janela,text=txtBaixo,font=("Arial",30,'bold'),fg = "green", bg=corFundoPadrao, width=30, height=3)
            lblBaixo.place(relx=.4, rely=.8, anchor="center")
            lblBaixo['text']=txtBaixo

            txtVermelho = "Voltar"
            #lblVermelho=Label(janela,text=txtVermelho,font=("Arial",30,'bold'),fg = "red", width=10, height=3)
            #lblVermelho.place(relx=.9, rely=.2, anchor="center")
            lblVermelho['text']=txtVermelho

            txtAmarelo = " "
            #lblAmarelo=Label(janela,text=txtAmarelo,font=("Arial",30,'bold'),fg = "yellow", width=10, height=3)
            #lblAmarelo.place(relx=.9, rely=.4, anchor="center")
            lblAmarelo['text']=txtAmarelo
            
            txtAzul = "Calibrar\nWebcam "
            #lblAzul=Label(janela,text=txtAzul,font=("Arial",30,'bold'),fg = "blue", width=10, height=3)
            #lblAzul.place(relx=.9, rely=.6, anchor="center")
            lblAzul['text']=txtAzul
            
            txtVerde = "Continuar"
            #lblVerde=Label(janela,text=txtVerde,font=("Arial",30,'bold'),fg = "green", width=10, height=3)
            #lblVerde.place(relx=.9, rely=.8, anchor="center")  
            lblVerde['text']=txtVerde
            janela.update()
            time.sleep(1)
        
        ### Tela JOGANDO    
        if (tela=='jogando' and telaEstado!='jogando'):
            telaEstado='jogando'
            
            txtCima="Resolva a operação"
            janela.lblCima=Label(janela,text=txtCima,font=("Arial",30,'bold'),fg = corTexto, bg=corFundo, width=30, height=3 )
            janela.lblCima.place(relx=.4, rely=.1, anchor="center")
            lblCima['text']=txtCima

            txtMeio = "......"  
            lblMeio=Label(janela,text=txtMeio,font=("Arial",60,'bold'),fg = corTexto, bg=corFundo, width=25, height=3)
            lblMeio.place(relx=.4, rely=.4, anchor="center")
            lblMeio['text']=txtMeio

            txtBaixo = "Pressione Verde\npara Confirmar"
            lblBaixo=Label(janela,text=txtBaixo,font=("Arial",30,'bold'),fg = "green", bg=corFundo, width=30, height=3)
            lblBaixo.place(relx=.4, rely=.8, anchor="center")
            lblBaixo['text']=txtBaixo

            txtVermelho = "Voltar"
            #lblVermelho=Label(janela,text=txtVermelho,font=("Arial",30,'bold'),fg = "red", width=10, height=3)
            #lblVermelho.place(relx=.9, rely=.2, anchor="center")
            lblVermelho['text']=txtVermelho

            txtAmarelo = " "
            #lblAmarelo=Label(janela,text=txtAmarelo,font=("Arial",30,'bold'),fg = "yellow", width=10, height=3)
            #lblAmarelo.place(relx=.9, rely=.4, anchor="center")
            lblAmarelo['text']=txtAmarelo
            
            txtAzul = " "
            #lblAzul=Label(janela,text=txtAzul,font=("Arial",30,'bold'),fg = "blue", width=10, height=3)
            #lblAzul.place(relx=.9, rely=.6, anchor="center")
            lblAzul['text']=txtAzul
            
            txtVerde = "Continuar"
            #lblVerde=Label(janela,text=txtVerde,font=("Arial",30,'bold'),fg = "green", width=10, height=3)
            #lblVerde.place(relx=.9, rely=.8, anchor="center")  
            lblVerde['text']=txtVerde
            janela.update()
            time.sleep(1)
        
        
        ### Tela Acertou    
        if (tela=='acertou' and telaEstado!='acertou'):
            telaEstado='acertou'
            
            txtCima=textoCerto
            janela.lblCima=Label(janela,text=txtCima,font=("Arial",30,'bold'),fg = corTexto, bg=corFundo, width=30, height=3 )
            janela.lblCima.place(relx=.4, rely=.1, anchor="center")
            lblCima['text']=txtCima

            txtMeio = "Você respondeu\n" + str(N1) +" "+operacao+" " +str(N2) +" = " + str(ResultadoEsperado) 
            lblMeio=Label(janela,text=txtMeio,font=("Arial",60,'bold'),fg = corTexto, bg=corFundo, width=25, height=3)
            lblMeio.place(relx=.4, rely=.4, anchor="center")
            lblMeio['text']=txtMeio

            txtBaixo = "Pressione Verde\npara Continuar"
            lblBaixo=Label(janela,text=txtBaixo,font=("Arial",30,'bold'),fg = "green", bg=corFundo, width=30, height=3)
            lblBaixo.place(relx=.4, rely=.8, anchor="center")
            lblBaixo['text']=txtBaixo

            txtVermelho = " "
            #lblVermelho=Label(janela,text=txtVermelho,font=("Arial",30,'bold'),fg = "red", width=10, height=3)
            #lblVermelho.place(relx=.9, rely=.2, anchor="center")
            lblVermelho['text']=txtVermelho

            txtAmarelo = " "
            #lblAmarelo=Label(janela,text=txtAmarelo,font=("Arial",30,'bold'),fg = "yellow", width=10, height=3)
            #lblAmarelo.place(relx=.9, rely=.4, anchor="center")
            lblAmarelo['text']=txtAmarelo
            
            txtAzul = " "
            #lblAzul=Label(janela,text=txtAzul,font=("Arial",30,'bold'),fg = "blue", width=10, height=3)
            #lblAzul.place(relx=.9, rely=.6, anchor="center")
            lblAzul['text']=txtAzul
            
            txtVerde = "Continuar"
            #lblVerde=Label(janela,text=txtVerde,font=("Arial",30,'bold'),fg = "green", width=10, height=3)
            #lblVerde.place(relx=.9, rely=.8, anchor="center")  
            lblVerde['text']=txtVerde
            janela.update()
            foto('PosC')
            time.sleep(1)
        
        
        ### Tela ERROU  
        if (tela=='errou' and telaEstado!='errou'):
            telaEstado='errou'
            
            txtCima=textoErrado
            janela.lblCima=Label(janela,text=txtCima,font=("Arial",30,'bold'),fg = corTexto, bg=corFundo, width=30, height=3 )
            janela.lblCima.place(relx=.4, rely=.1, anchor="center")
            lblCima['text']=txtCima

            txtMeio = "Você respondeu " + str(RespUsuarioTot) + "\nO correto seria " + str(N1) +" "+operacao+" " +str(N2) +" = " + str(ResultadoEsperado) 
            lblMeio=Label(janela,text=txtMeio,font=("Arial",60,'bold'),fg = corTexto, bg=corFundo, width=25, height=3)
            lblMeio.place(relx=.4, rely=.4, anchor="center")
            lblMeio['text']=txtMeio

            txtBaixo = "Pressione Verde\npara Continuar"
            lblBaixo=Label(janela,text=txtBaixo,font=("Arial",30,'bold'),fg = "green", bg=corFundo, width=30, height=3)
            lblBaixo.place(relx=.4, rely=.8, anchor="center")
            lblBaixo['text']=txtBaixo

            txtVermelho = " "
            #lblVermelho=Label(janela,text=txtVermelho,font=("Arial",30,'bold'),fg = "red", width=10, height=3)
            #lblVermelho.place(relx=.9, rely=.2, anchor="center")
            lblVermelho['text']=txtVermelho

            txtAmarelo = " "
            #lblAmarelo=Label(janela,text=txtAmarelo,font=("Arial",30,'bold'),fg = "yellow", width=10, height=3)
            #lblAmarelo.place(relx=.9, rely=.4, anchor="center")
            lblAmarelo['text']=txtAmarelo
            
            txtAzul = " "
            #lblAzul=Label(janela,text=txtAzul,font=("Arial",30,'bold'),fg = "blue", width=10, height=3)
            #lblAzul.place(relx=.9, rely=.6, anchor="center")
            lblAzul['text']=txtAzul
            
            txtVerde = "Continuar"
            #lblVerde=Label(janela,text=txtVerde,font=("Arial",30,'bold'),fg = "green", width=10, height=3)
            #lblVerde.place(relx=.9, rely=.8, anchor="center")  
            lblVerde['text']=txtVerde
            janela.update()
            foto('PosE')
            time.sleep(1)
        
        
        ### Tela Resultados 
        if (tela=='resultados' and telaEstado!='resultados'):
            telaEstado='resultados'
            
            txtCima="RESULTADOS\n" + str(cicloAtual-1) + " tentativas"
            janela.lblCima=Label(janela,text=txtCima,font=("Arial",30,'bold'),fg = corTexto, bg=corFundo, width=30, height=3 )
            janela.lblCima.place(relx=.4, rely=.1, anchor="center")
            lblCima['text']=txtCima

            txtMeio = "Acertou " + str(acertos) + "\nErrou  " + str(erros)
            lblMeio=Label(janela,text=txtMeio,font=("Arial",60,'bold'),fg = corTexto, bg=corFundo, width=25, height=3)
            lblMeio.place(relx=.4, rely=.4, anchor="center")
            lblMeio['text']=txtMeio

            txtBaixo = "Pressione Verde\npara o Próximo Jogador"
            lblBaixo=Label(janela,text=txtBaixo,font=("Arial",30,'bold'),fg = "green", bg=corFundo, width=30, height=3)
            lblBaixo.place(relx=.4, rely=.8, anchor="center")
            lblBaixo['text']=txtBaixo

            txtVermelho = " "
            #lblVermelho=Label(janela,text=txtVermelho,font=("Arial",30,'bold'),fg = "red", width=10, height=3)
            #lblVermelho.place(relx=.9, rely=.2, anchor="center")
            lblVermelho['text']=txtVermelho

            txtAmarelo = " "
            #lblAmarelo=Label(janela,text=txtAmarelo,font=("Arial",30,'bold'),fg = "yellow", width=10, height=3)
            #lblAmarelo.place(relx=.9, rely=.4, anchor="center")
            lblAmarelo['text']=txtAmarelo
            
            txtAzul = " "
            #lblAzul=Label(janela,text=txtAzul,font=("Arial",30,'bold'),fg = "blue", width=10, height=3)
            #lblAzul.place(relx=.9, rely=.6, anchor="center")
            lblAzul['text']=txtAzul
            
            txtVerde = "Proximo\nJogador"
            #lblVerde=Label(janela,text=txtVerde,font=("Arial",30,'bold'),fg = "green", width=10, height=3)
            #lblVerde.place(relx=.9, rely=.8, anchor="center")  
            lblVerde['text']=txtVerde
            janela.update()
            foto('PosR')
            time.sleep(1)
        
        
            
        #####################################################################################
        ################ Botoes das telas
        ### Tela Inicial
        if (telaEstado=='inicial' and estadoBotaoVermelho==1):
            tela='desligar'
        if (telaEstado=='inicial' and estadoBotaoVerde==1):
            tela='nivel'
        if (telaEstado=='inicial' and estadoBotaoAzul==1):
            os.system ('fswebcam -r640x480 "capturas/1teste.jpg"')
            #time.sleep(1)
            os.system('gpicview "capturas/1teste.jpg" &')   
            time.sleep(3)
            os.system('sudo killall -9 gpicview')
            
                
        ### Tela Desligar   
        if(telaEstado=='desligar' and estadoBotaoVermelho==1):
            tela='inicial'
        if (telaEstado=='desligar' and estadoBotaoVerde==1): 
            desligaSistema()
        if (telaEstado=='desligar' and estadoBotaoAmarelo==1): 
            sairSistema()
            
        ### Tela Nível  
        if(telaEstado=='nivel' and estadoBotaoVermelho==1):
            tela='inicial'  
        if(telaEstado=='nivel' and estadoBotaoAmarelo==1):
            tela='operacao'
            nivel=31
        if(telaEstado=='nivel' and estadoBotaoAzul==1):
            tela='operacao'
            nivel=22
        if(telaEstado=='nivel' and estadoBotaoVerde==1):
            tela='operacao'
            nivel=21    
            
            
        ### Tela Selecionar Operação
        if(telaEstado=='operacao' and estadoBotaoVermelho==1):
            tela='nivel'    
        if(telaEstado=='operacao' and estadoBotaoAmarelo==1):
            tela='codigo'
            operacao='+'    
        if(telaEstado=='operacao' and estadoBotaoAzul==1):
            tela='codigo'
            operacao='-'
        if(telaEstado=='operacao' and estadoBotaoVerde==1):
            tela='codigo'
            operacao='x'
            
        ### Tela Codigo do aluno
        if(telaEstado=='codigo' and estadoBotaoVermelho==1):
            tela='operacao' 
        if(telaEstado=='codigo' and estadoBotaoVerde==1):
            tela='jogando'
            ####
            conexaoBancoAjuste=sqlite3.connect('ajuste.db')
            bancoAjuste=conexaoBancoAjuste.cursor()
            sqlUp="UPDATE tabAjuste SET valor=" + str(5) + " where id=1"
            bancoAjuste.execute(sqlUp)
            conexaoBancoAjuste.commit()
            conexaoBancoAjuste.close()
            ###
            #print('################################ Ajustando o Ajuste Tela COD Aluno. . . ' +str(ajuste))
            cicloMax=5
            cicloAtual=1
            acertos=0
            erros=0
            respondeuCerto=None
            jaInverteu=None
            precisaInverter=None
            # ler cartões dos códigos dos alunos
            lerCartao_Dez()
            lerCartao_Uni()
            codigoUsuario = RespUsuarioDez+RespUsuarioUni
            print ("Código Usuário = " +str(codigoUsuario))
            time.sleep(1)
            
             
             
        if (telaEstado=='codigo' and estadoBotaoAzul==1):
            os.system ('fswebcam -r640x480 "capturas/1teste.jpg"')
            #time.sleep(1)
            os.system('gpicview "capturas/1teste.jpg" &')   
            time.sleep(3)
            os.system('sudo killall -9 gpicview')
            
        
        ### Tela Jogando
        if(telaEstado=='jogando' and estadoBotaoVermelho==1):
            tela='codigo'
            sorteioEstado=None  
        if(telaEstado=='jogando' and estadoBotaoVerde==1 and sorteioEstado=='OK'):
            #### Tela Jogando + Verifica Resposta
            RespUsuarioDez=0
            RespUsuarioUni=0
            cicloAtual=cicloAtual+1
            lerCartao_Dez()
            lerCartao_Uni() 
            
            
                    
            RespUsuarioTot=RespUsuarioDez+RespUsuarioUni
            print("<<<<<<<<<<<<<<<<< Resposta do usuário : " + str(RespUsuarioTot))

            if (RespUsuarioTot==ResultadoEsperado):
                tela='acertou'
                acertos=acertos+1
                print(" >>>>>>>> Acertou !")  
            else:
                tela='errou'
                erros=erros+1
                print(" ######## Errou !")
                if (cicloAtual<=cicloMax and precisaInverter==None):
                    precisaInverter='S'

            janela.update()
        
        
        
        
        ### Tela Acertou
        if (telaEstado=='acertou' and estadoBotaoVerde==1):
            if (cicloAtual<=cicloMax):
                tela='jogando'
            else:
                tela='resultados'   
                
            sorteioEstado=None
            
        ### Tela Errou
        if (telaEstado=='errou' and estadoBotaoVerde==1):
            if (cicloAtual<=cicloMax):
                tela='jogando'
            else:
                tela='resultados'
                
            sorteioEstado=None
        
        ### Tela Resultados
        if (telaEstado=='resultados' and estadoBotaoVerde==1):
            tela='codigo'
            
            
            
        #### Tela Jogando + Sorteio
        if (tela=='jogando' and telaEstado=='jogando' and sorteioEstado!='OK'):
            sorteioEstado='OK'
            sorteioNumeros()
            
        
            
        janela.update() 
        
     

##########################################
### Prog Principal
print("Iniciando")
janela = tk.Tk() # Criando objeto janela

### Definições gerais da Janela
#janela.attributes('-fullscreen', True) # para deixar em tela cheia
m = janela.maxsize()
janela.geometry('{}x{}+0+0'.format(*m))
janela.title('Matemática com Emoção - Vansan')

#janela.config(bg='light blue') #cor de fundo da janela
image=tk.PhotoImage(file="paisagem.gif") #se estiver na mesma pasta
#image=tk.PhotoImage(file="E:\\OneDrive\\OneDrive - Centro Paula Souza - Etec\\User-Windows\\Desktop\\paisagem.gif") #se estiver pasta diferente
image=image.subsample(1,1)
labelimage=tk.Label(image=image)
labelimage.place(x=0,y=0,relwidth=1.0,relheight=1.0)
####


#######################
## Iniciando Leituras
thread_MicroControlador = threading.Thread(target=MicroControlador,args=("MicroControlador",))
thread_MicroControlador.start()

thread_Telas = threading.Thread(target=gerenciador_de_Telas,args=("gerenciador_de_Telas",))
thread_Telas.start()

janela.mainloop()
## FIM
