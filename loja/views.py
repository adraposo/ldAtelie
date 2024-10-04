from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
import uuid
from .utils import filtrar_produtos, preco_min_max, ordenar_produtos, enviar_email_compra, exportar_csv
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from datetime import datetime
from .api_mpago import criar_pagamento

# Create your views here.

def homepage(request):
    banners = Banner.objects.filter(ativo=True)
    context = {"banners": banners}
    return render(request, 'homepage.html', context)

def loja(request, param=None):

    produtos = Produto.objects.filter(ativo=True)
    if param:
        if "-" in param:
            produtos = filtrar_produtos(produtos, param)
        elif (param == "maisvendidos" or param == "menorpreco" or param == "maiorpreco"): 
                produtos = ordenar_produtos(produtos, param)
        else:
                produtos = filtrar_produtos(produtos, param)
    
    minimo, maximo = preco_min_max(produtos) 
    itens = ItemEstoque.objects.filter(quantidade__gt=0, produto__in=produtos)
    tamanhos = itens.values_list("tamanho", flat=True).distinct()
    ids_categorias = produtos.values_list("categoria", flat=True).distinct()
    categorias = Categoria.objects.filter(id__in=ids_categorias)   
    ids_tipos = produtos.values_list("tipo", flat=True).distinct()
    tipos = Tipo.objects.filter(id__in=ids_tipos)
    
    if request.method == "POST":

        dados = request.POST.dict()
        produtos = produtos.filter(preco__gte=dados.get("preco_min"), preco__lte=dados.get("preco_max"))

        if "tamanho" in dados:
            itens = ItemEstoque.objects.filter(produto__in=produtos, tamanho=dados.get("tamanho"))
            # tamanhos = itens.values_list("tamanho", flat=True).distinct()
            ids_produtos = itens.values_list("produto", flat=True).distinct()
            produtos = produtos.filter(id__in=ids_produtos)

        if "categoria" in dados:
            produtos = produtos.filter(categoria__slug=dados.get("categoria"))
            # ids_categorias = produtos.values_list("categoria", flat=True).distinct()
            # categorias = Categoria.objects.filter(id__in=ids_categorias)  

        if "tipo" in dados:
            produtos = produtos.filter(tipo__slug=dados.get("tipo"))
            # ids_tipos = produtos.values_list("tipo", flat=True).distinct()
            # tipos = Tipo.objects.filter(id__in=ids_tipos)


        ordem = request.GET.get("param", "menorpreco")
    
    context = {"produtos": produtos, "minimo": minimo, "maximo": maximo, "tamanhos": tamanhos,
               "categorias": categorias, "tipos": tipos}
    return render(request, 'loja.html', context)

def det_produto(request, id_produto, id_cor=None):

    tem_estoque = False
    cores = {}
    tamanhos = {}
    cor_selecionada = None
    produto = Produto.objects.get(id=id_produto)
    itens_estoque = ItemEstoque.objects.filter(produto=produto, quantidade__gt=0)

    if len(itens_estoque) > 0:
        tem_estoque = True
        cores = {item.cor for item in itens_estoque}
        if id_cor:
            itens_estoque = ItemEstoque.objects.filter(produto=produto, quantidade__gt=0, cor__id=id_cor)
            tamanhos = {item.tamanho for item in itens_estoque}
            cor_selecionada = Cor.objects.get(id=id_cor)
            # desc_cor_selecionada = cor_selecionada.descricao

    similares = Produto.objects.filter(categoria__id=produto.categoria_id, tipo__id=produto.tipo.id).exclude(id=produto.id)[:4]
    context = {"produto": produto, "itens_estoque": itens_estoque, "tem_estoque": tem_estoque, "cores": cores, "tamanhos": tamanhos,
               "cor_selecionada": cor_selecionada, "similares": similares 
               }
    return render(request, 'det_produto.html',context)

def adicionar_carrinho(request, id_produto):
    if request.method == "POST" and id_produto:
        dados = request.POST.dict()
        tamanho = dados.get("tamanho")
        id_cor = dados.get("cor")

        if not tamanho:
            return redirect('loja')
        
        resposta = redirect('carrinho')

        if request.user.is_authenticated:
            cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao")
            else:
                id_sessao = str(uuid.uuid4())
                resposta.set_cookie(key="id_sessao", value=id_sessao)

            print("id_sessao = ", id_sessao)
            cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
        
        pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
        item_estoque = ItemEstoque.objects.get(produto__id=id_produto, tamanho=tamanho, cor__id=id_cor)
        item_pedido, criado = ItensPedido.objects.get_or_create(item_estoque=item_estoque, pedido=pedido)
        item_pedido.quantidade += 1
        item_pedido.save()
        return resposta
    else:
        return redirect('loja')
    
def remover_carrinho(request, id_produto):
    if request.method == "POST" and id_produto:
        dados = request.POST.dict()

        tamanho = dados.get("tamanho")
        id_cor = dados.get("cor")
        if not tamanho:
            return redirect('loja')
        
        resposta = redirect('carrinho')

        if request.user.is_authenticated:
            cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao")
            else:
                id_sessao = str(uuid.uuid4())
                resposta.set_cookie(key="id_sessao", value=id_sessao)

            cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
        
        pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
        item_estoque = ItemEstoque.objects.get(produto__id=id_produto, tamanho=tamanho, cor__id=id_cor)
        item_pedido, criado = ItensPedido.objects.get_or_create(item_estoque=item_estoque, pedido=pedido)
        item_pedido.quantidade -= 1
        item_pedido.save()
        if item_pedido.quantidade < 1:
            item_pedido.delete()
        return resposta
    else:
        return redirect('loja')

def carrinho(request):
    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        if request.COOKIES.get("id_sessao"):
            id_sessao = request.COOKIES.get("id_sessao")
            cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
        else:
            context = {"cliente_existente": False, "itens_pedido": None, "pedido": None}
            return render(request, 'carrinho.html', context)

    pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
    itens_pedido = ItensPedido.objects.filter(pedido=pedido)
    context = {"cliente_existente": True, "itens_pedido": itens_pedido, "pedido": pedido }

    return render(request, 'carrinho.html', context)

def checkout(request):
    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        if request.COOKIES.get("id_sessao"):
            id_sessao = request.COOKIES.get("id_sessao")
            cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
        else:
            return redirect("loja")

    pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=True)
    enderecos = Endereco.objects.filter(cliente=cliente)
    
    context = {"pedido": pedido, "enderecos": enderecos, "erro": None }

    return render(request, 'checkout.html', context)

def finalizarpedido(request, id_pedido):
    if request.method == "POST":
        erro = None
        dados = request.POST.dict()
        total = dados.get("total")
        total = float(total.replace(",", "."))
        pedido = Pedido.objects.get(id=id_pedido)

        if float(total) != float(pedido.preco_total):

        # if total != pedido.preco_total:
            erro = "preco"

        if not "endereco" in dados:
            erro = "endereco"
        else:
            id_endereco = dados.get("endereco")
            
            endereco = Endereco.objects.get(id = id_endereco)
            pedido.endereco = endereco

        if not request.user.is_authenticated:

            email = dados.get("email")
            try:
                validate_email(email)
            except ValidationError:
                erro = "email"
            if not erro:
                clientes = Cliente.objects.filter(email=email)
                if clientes:
                    pedido.cliente = clientes[0]
                else:
                    pedido.cliente.email = email
                    pedido.cliente.save()

        if erro:
            enderecos = Endereco.objects.filter(cliente=pedido.cliente)
            context = {"erro": erro, "pedido": pedido, "enderecos": enderecos}
            return render(request, "checkout.html", context)
        else: 
            codigo_transacao = f"{pedido.id}-{datetime.now().timestamp()}"
            pedido.codigo_transacao = codigo_transacao
            pedido.save()
            itens_pedido = ItensPedido.objects.filter(pedido=pedido)
            link = request.build_absolute_uri(reverse("finalizarpagamento"))
            link_pagamento, id_pagamento = criar_pagamento(itens_pedido, link)
            pagamento = Pagamento.objects.create(id_pagamento=id_pagamento, pedido=pedido)
            pagamento.save()
            return redirect(link_pagamento)
    else:
        return redirect('loja')

def finalizarpagamento(request):
    # {'collection_id': '87916523939', 'collection_status': 'approved', 'payment_id': '87916523939', 'status': 'approved', 
    # 'external_reference': 'null', 'payment_type': 'credit_card', 'merchant_order_id': '22970709860', 
    # 'preference_id': '1991098108-a83b8f85-57a1-435b-8dff-ddf45996ac02', 'site_id': 'MLB', 'processing_mode': 'aggregator', 'merchant_account_id': 'null'}

    dados = request.GET.dict()
    status = dados.get("status")
    id_pagamento = dados.get("preference_id")
    if status == "approved":
        pagamento = Pagamento.objects.get(id_pagamento=id_pagamento)
        pagamento.aprovado = True
        pedido = pagamento.pedido
        pedido.finalizado = True
        pedido.data_finalizacao = datetime.now()
        pedido.save()
        pagamento.save()
        enviar_email_compra(pedido)

        if request.user.is_authenticated:
            return redirect("meus_pedidos")
        else:
            return redirect("pedido_aprovado", pedido.id)
    else:
        return redirect("checkout")
    

def pedidoaprovado(request, id_pedido):
    pedido = Pedido.objects.get(id=id_pedido)
    context = {"pedido": pedido}
    return render (request, "pedidoaprovado.html", context)

def adicionar_endereco(request):
    if request.method == "POST":
        #tratar envio do form
        if request.user.is_authenticated:
            cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao")
                cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
            else:
                return redirect("loja")

        dados = request.POST.dict()
        endereco = Endereco.objects.create(cliente=cliente, 
                                           rua=dados.get("rua"),
                                           numero=int(dados.get("numero")),
                                           complemento=dados.get("complemento"),
                                           bairro=dados.get("bairro"),
                                           cidade=dados.get("cidade"),
                                           estado=dados.get("estado"),
                                           cep=dados.get("cep"),
                                           )
        endereco.save()
        return redirect("checkout")
    
    else: 
        context = {}
        return render(request, 'endereco.html', context)

def criarconta(request):
    erro = None
    if request.user.is_authenticated:
        return redirect('loja')
    if request.method == 'POST':
        dados = request.POST.dict()
        if "email" in dados and "senha" in dados and "confirmacaosenha" in dados:
            email = dados.get("email")
            senha = dados.get("senha")
            confirmacaosenha = dados.get("confirmacaosenha")
            try:
                validate_email(email)
            except ValidationError:
                erro = "email_invalido"
            if senha == confirmacaosenha:
                usuario, criado = User.objects.get_or_create(username=email, email=email)
                if not criado:
                    erro = "usuario_existente"
                else:
                    usuario.set_password(senha)
                    usuario.save()
                    # Fazer login
                    usuario = authenticate(request, username=email, password=senha)
                    login(request, usuario)
                    
                    if request.COOKIES.get("id_sessao"):
                        id_sessao = request.COOKIES.get("id_sessao")
                        cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
                    else:
                        cliente, criado = Cliente.objects.get_or_create(email=email)
                    cliente.usuario = usuario
                    cliente.email = email
                    cliente.nome = email
                    cliente.save()
                    return redirect("loja")
            else:
                erro = "senhas_diferentes"
        else:
            erro = "preenchimento"
    context = { "erro": erro }
            
    return render(request, 'usuario/criarconta.html', context )

@login_required
def minhaconta(request):
    erro = None
    alterado = False
    if  request.method == "POST":
        dados = request.POST.dict()
        if "senha_atual" in dados:
            #alterou senha
            senha_atual = dados.get("senha_atual")
            nova_senha = dados.get("nova_senha")
            confirmacao_senha = dados.get("confirmacao_senha")
            if nova_senha == confirmacao_senha:
                #verificar senha atual
                usuario = authenticate(request, username=request.user.email, password=senha_atual)
                if usuario:
                    usuario.set_password(nova_senha)
                    usuario.save()
                    alterado = True
                else:
                    erro = "senha_incorreta"
            else:
                erro = "senhas_diferentes"
                
        elif "email" in dados:
            #alterou dados pessoais
            nome = dados.get("nome")
            email = dados.get("email")
            celular = dados.get("celular")
            if email != request.user.email:
                usuarios = User.objects.filter(email=email)
                if len(usuarios) > 0:
                    erro = "email_existente"
            if not erro:
                cliente = request.user.cliente
                cliente.email = email
                request.user.email = email
                request.user.username = email
                cliente.nome = nome
                cliente.celular = celular
                cliente.save()
                request.user.save()
                alterado = True
        else:
            erro = "formulario_invalido"

    context = {"erro": erro, "alterado": alterado}
    return render(request, 'usuario/minhaconta.html', context)

@login_required
def meus_pedidos(request):
    cliente = request.user.cliente
    meuspedidos = Pedido.objects.filter(finalizado=True, cliente=cliente).order_by("-data_finalizacao")
    context = {"meuspedidos": meuspedidos }
    return render(request, 'usuario/meuspedidos.html', context)

def fazerlogin(request):
    erro = False
    if request.user.is_authenticated:
        return redirect("loja")
        
    if request.method == 'POST':
        dados = request.POST.dict()
        if "email" in dados and "senha" in dados:
            email = dados.get("email")
            senha = dados.get("senha")
            usuario = authenticate(request, username=email, password=senha)
            if usuario:
                login(request, usuario)
                return redirect('loja')
            else:
                erro = True
        else:
            erro = True
    
    context = {"erro": erro}

    return render(request, 'usuario/fazerlogin.html', context)

@login_required
def fazerlogout(request):
    logout(request)
    return redirect('fazerlogin')

@login_required
def gerenciarloja(request):
    context = {}
    if request.user.groups.filter(name="equipe").exists():
        pedidos_finalizados = Pedido.objects.filter(finalizado=True)
        qtde_pedidos = len(pedidos_finalizados)
        faturamento = sum(pedido.preco_total for pedido in pedidos_finalizados)
        qtdeprodutosvendidos = sum(pedido.quantidade_total for pedido in pedidos_finalizados)
        context = { "qtde_pedidos": qtde_pedidos, "qtdeprodutosvendidos": qtdeprodutosvendidos, "faturamento": faturamento }
        return render(request, 'interno/gerenciarloja.html', context)
    else:
        redirect("loja")

@login_required
def exportar_relatorio(request, relatorio):

    if request.user.groups.filter(name="equipe").exists():
        if  relatorio == "pedidos":
            informacoes = Pedido.objects.filter(finalizado=True)
        elif relatorio == "clientes":
            informacoes = Cliente.objects.all()
        elif relatorio == "enderecos":
            informacoes = Endereco.objects.all()

        return exportar_csv(informacoes)
    else:
        return redirect('gerenciarloja')

