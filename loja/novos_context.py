from .models import Pedido, ItensPedido, Cliente, Categoria, Tipo

def carrinho (request):
    
    qtde_prod_carrinho = 0
    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        if request.COOKIES.get("id_sessao"):
            id_sessao = request.COOKIES.get("id_sessao")
            cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
        else:
            return {"qtde_prod_carrinho": qtde_prod_carrinho}

    pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
    itens_pedido = ItensPedido.objects.filter(pedido=pedido)
    for item in itens_pedido:
        qtde_prod_carrinho += item.quantidade

    return {"qtde_prod_carrinho": qtde_prod_carrinho}

def categorias_tipos(request):
    categorias_nav = Categoria.objects.all()
    tipos_nav = Tipo.objects.all()
    return {"categorias_nav": categorias_nav, "tipos_nav": tipos_nav}

def faz_parte_equipe(request):
    equipe = False
    if request.user.is_authenticated:
        if request.user.groups.filter(name="equipe").exists():
            equipe = True

    return {"equipe": equipe}