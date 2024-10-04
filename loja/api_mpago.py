import mercadopago

public_key = "APP_USR-afbecd63-3709-4e76-b7e5-d2a3a2ea9f01"
token = "APP_USR-7564678687381689-091315-94d50ac809f6472fadd7adfa30460212-1991098108"

def criar_pagamento(itens_pedido, link):
    # Adicione as credenciais
    sdk = mercadopago.SDK(token)

    # Cria um item na preferência
    itens = []
    for item in itens_pedido:
        myitem = item.item_estoque.produto.descricao
        quantidade = int(item.quantidade)
        unit_price = float(item.item_estoque.produto.preco)
        itens.append({
            "title": myitem,
            "quantity": quantidade,
            "unit_price": unit_price,
        })

    preference_data = {
        "items": itens,

        "auto_return": "all",
        
        "back_urls": {
                "success": link,
                "pending": link,
                "failure": link,
            }
                     }

    resposta = sdk.preference().create(preference_data)
    print("preference_data--> ", preference_data)
    print (" ")
    print ("resposta response--> ", resposta["response"])
    link_pagamento = resposta["response"]["init_point"]
    id_pagamento = resposta["response"]["id"]
    print (" ")
    return link_pagamento, id_pagamento
    






