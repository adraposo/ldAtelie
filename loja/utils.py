from django.db.models import Min, Max
from django.core.mail import send_mail
from django.http import HttpResponse
import csv

def filtrar_produtos(produtos, param):
    # print( "vai filtrar")
    if param:
        if "-" in param:
            categoria, tipo = param.split("-")
            produtos = produtos.filter(categoria__slug=categoria, tipo__slug=tipo)    
        else:
            produtos = produtos.filter(categoria__slug=param)
    return produtos

def preco_min_max(produtos):
    minimo = 0
    maximo = 0

    if len(produtos) > 0:
        minimo = list(produtos.aggregate(Min("preco")).values())[0]
        minimo = round(minimo,2)
        maximo = list(produtos.aggregate(Max("preco")).values())[0]
        maximo = round(maximo,2)
    return (minimo, maximo)

def ordenar_produtos(produtos, ordem):
    # print ("produtos-->" , produtos)
    # print("ordem-->", ordem)
    if ordem == "menorpreco":
        produtos = produtos.order_by("preco")
    elif ordem == "maiorpreco":
        produtos = produtos.order_by("-preco")
    elif ordem == "maisvendidos":
        lista_produtos = []
        for produto in produtos:
            lista_produtos.append((produto.qtdetotalvendas(), produto))
        lista_produtos = sorted(lista_produtos, reverse=True, key=lambda x: x[0])
        produtos = [item[1] for item in lista_produtos]

    return produtos

def enviar_email_compra(pedido):

    email = pedido.cliente.email
    assunto = f"Pedido aprovado : { pedido.id }"
    corpo = f""" Parabéns!!! Seu pedido foi aprovado.
    ID do pedido : {pedido.id}
    Valor total : {pedido.preco_total}"""
    remetente = "adwilson.raposo@gmail.com"
    send_mail(assunto, corpo, remetente, [email])

    return pedido

def exportar_csv(informacoes):
    # print(informacoes.model)
    # print(informacoes.model._meta.fields)
    colunas = informacoes.model._meta.fields
    nomes_colunas = [coluna.name for coluna in colunas]
    resposta = HttpResponse(content_type="text/csv")
    resposta["Content-Disposition"] = "attachment; filename=export.csv"

    criador_csv = csv.writer(resposta, delimiter=";")

    criador_csv.writerow(nomes_colunas)

    for linha in informacoes.values_list():
        criador_csv.writerow(linha)

    return resposta


