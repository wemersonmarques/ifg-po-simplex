# Importar bibliotecas
from flask import Flask, request, render_template
import json
import pandas as pd
import collections
import numpy as np

# Criar o app Flask
app = Flask(__name__)

# Cria a linha de cada restrição recebendo o dicionário da restrição e quantidade de folgas
def construir_restricao(restricao, qtd_folgas) : 
    linha = collections.OrderedDict()
    # Valor de Z nas restrições sempre é zero
    linha['z'] = [0]
    for chave, valor in restricao.items():
        if chave != 'b':
            linha[chave] = valor

    if (linha['op'] == '<=') or (linha['op'] == '>='):
        linha['xF' + str(qtd_folgas + 1)] = 1
        qtd_folgas += 1
        
    del(linha['op'])
    linha['b'] = restricao['b']
    
    return linha, qtd_folgas


def identificar_linha_sai(tabela, coluna_entra):
    # Remover a primeira linha (função objetivo)
    tabela = tabela.drop([0])
    # Cria nova coluna do resultado da divisão entre 'b' e a coluna que entra (parâmetro)
    tabela['b/coluna_entra'] = tabela['b'] / tabela[coluna_entra]
    # Encontra o menor valor da coluna de divisão
    menor_divisao = np.min(tabela['b/coluna_entra'])
    # Identifica o primeiro índice da linha que possui o valor igual ao da menor divisão
    indice = list(tabela.loc[tabela['b/coluna_entra'] == menor_divisao].index)[0]
    
    return indice
    
def calcular_nova_linha_pivo(tabela, linha_sai, elemento_pivo) :
    tabela_temp = tabela.copy()
    tabela_temp.iloc[linha_sai] = tabela_temp.loc[linha_sai]/elemento_pivo
    return tabela_temp.iloc[linha_sai]
    
def calcular_nova_tabela(tabela, linha_pivo, coluna_entra, linha_sai):
    # Remove a primeira linha da tabela original (função objetivo)
    temp_tabela = tabela.copy()
    temp_tabela = temp_tabela.drop([linha_sai])
    # Copia a tabela existente para uma nova
    nova_tabela = tabela.copy()
    # Remove todas as linhas para manter a estrutura
    nova_tabela.drop(nova_tabela.index, inplace=True)
    
    # Calcula novas linhas
    for i in range(0, len(tabela)):
        if not linha_pivo.name == i:
            nova_linha = linha_pivo * (tabela[coluna_entra][i] * -1)
            # Adiciona com a linha correspondente do indice da tabela original6
            nova_linha = nova_linha + tabela.iloc[i]
            # Adiciona a nova linha calculada na nova tabela
            nova_tabela = nova_tabela.append(nova_linha, ignore_index=True)
        else:
            nova_tabela = nova_tabela.append(linha_pivo, ignore_index=True)
    
    # Adiciona a nova linha pivô na nova tabela
    
    return nova_tabela
    
def is_resultado_otimo(nova_tabela):
    menor_valor = min(nova_tabela.iloc[0])
    if menor_valor < 0:
        return False
    return True

def identificar_coluna_entra(tabela, lista_variaveis):
    primeira_linha = tabela.iloc[0]
    lista_valores = []
    
    
    for chave, valor in primeira_linha.items():
        if chave in lista_variaveis:
            lista_valores.append(valor)    
    menor_valor = np.min(lista_valores)
   
    
    for chave, valor in primeira_linha.items():
        if chave in lista_variaveis:
            if menor_valor == valor:
                menor_chave = chave
                break
    
    return menor_chave
        

@app.route("/simplex", methods=['GET'])
def simplex():
    for chave in request.args:
        valor = request.args.get(chave)
        print(chave, valor)
        print('-----')


    # FUNCAO OBJETVIO
    z = collections.OrderedDict({'x1':10,'x2':12})
    lista_variaveis = z.keys()
    print(lista_variaveis)
    print(z)
    
    ####
    
    restricoes = [collections.OrderedDict({'x1':1,'x2':1,'op':'<=','b':100}),
                    collections.OrderedDict({'x1':1,'x2':3,'op':'<=','b':270})]
    print(restricoes)

    ####
    
    # Valor de Z na função objetivo sempre é 1
    linha_obj = collections.OrderedDict({'z': [1]})

    for chave, valor in z.items():
        linha_obj[chave] = [valor*(-1)]

    linha_obj['b'] = [0]
    linha_obj = pd.DataFrame.from_dict(linha_obj)
    linha_obj
    
    ####
    
    # Inserindo cada restrições, da lista restrições, na tabela criada anteriormente
    qtd_folgas = 0
    # Tratamento para 'resetar' a tabela em tempo de execução
    tabela = linha_obj.copy()
    for restricao in restricoes:
        linha, qtd_folgas = construir_restricao(restricao, qtd_folgas)
        linha = pd.DataFrame.from_dict(linha)
        tabela = tabela.append(linha, ignore_index=True)
    tabela = tabela.fillna(0)
    print(tabela)
    
    #####
    coluna_entra = identificar_coluna_entra(tabela, lista_variaveis)

    linha_sai = identificar_linha_sai(tabela, coluna_entra)

    # Encontra o elemento pivô da interseção entre coluna que entra e linha que sai
    elemento_pivo = tabela[coluna_entra][linha_sai]
    linha_pivo = tabela.loc[linha_sai]
    nova_linha_pivo = calcular_nova_linha_pivo(tabela, linha_sai, elemento_pivo)
    nova_tabela = calcular_nova_tabela(tabela, nova_linha_pivo, coluna_entra, linha_sai)
    print('Nova tabela primeira execucao')
    print(nova_tabela)
    #

    i = 0

    while (not is_resultado_otimo(nova_tabela) and i < len(tabela)):
        print('-------------- CALCULANDO NOVA TABELA ' + str(i) + ' --------------')
        # Calcular nova linha
        coluna_entra = identificar_coluna_entra(nova_tabela, lista_variaveis)
        linha_sai = identificar_linha_sai(nova_tabela, coluna_entra)
        # Encontra o elemento pivô da interseção entre coluna que entra e linha que sai
        elemento_pivo = nova_tabela[coluna_entra][linha_sai]
        nova_linha_pivo = calcular_nova_linha_pivo(nova_tabela, linha_sai, elemento_pivo)
        
        nova_tabela = calcular_nova_tabela(nova_tabela, nova_linha_pivo, coluna_entra, linha_sai)
        i += 1;
        print(nova_tabela)
        print('-----------------------------')

    print('Encontrei um resultado ótimo!')
    print('Valor da maximização: ' + str(nova_tabela['b'][0]))
    print('Valor de x1: ' + str(nova_tabela['b'][1]))
    print('Valor de x2: ' + str(nova_tabela['b'][2]))
            
    
    

    return render_template('simplex.html', valor_x1=999, valor_x2=888, valor_max = 7777)

# Página inicial
@app.route("/")
def home():
    return render_template('simplex.html')


# Se o arquivo for executado, executar o app
# Acesse via navegador 127.0.0.1:5000 ou seuIp:5000 (exemplo: 10.239.68.19:5000)
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
