from django.urls import path
from django.contrib.auth import views
from .views import *

urlpatterns = [

    path('', homepage, name="homepage"),
    path('loja/', loja, name="loja"),
    path('loja/<str:param>/', loja, name="loja"),
    path('produto/<int:id_produto>/', det_produto, name="det_produto"),    
    path('produto/<int:id_produto>/<int:id_cor>/', det_produto, name="det_produto"),    
 
    path('carrinho/', carrinho, name="carrinho"),
    path('checkout/', checkout, name="checkout"),
    path('removercarrinho/<int:id_produto>/', remover_carrinho, name="remover_carrinho"),    
    path('adicionarcarrinho/<int:id_produto>/', adicionar_carrinho, name="adicionar_carrinho"),    
    path('adicionar_endereco/', adicionar_endereco, name="adicionar_endereco"),    
    path('finalizarpedido/<int:id_pedido>/', finalizarpedido, name="finalizarpedido"),    
    path('finalizarpagamento/', finalizarpagamento, name="finalizarpagamento"),
    path('pedidoaprovado/<int:id_pedido>/', pedidoaprovado, name="pedidoaprovado"),    
    
    path('criarconta/', criarconta, name="criarconta"),
    path('minhaconta/', minhaconta, name="minhaconta"),
    path('meuspedidos/', meus_pedidos, name="meus_pedidos"),
    path('fazerlogin/', fazerlogin, name="fazerlogin"),
    path('fazerlogout/', fazerlogout, name="fazerlogout"),

    path('gerenciarloja/', gerenciarloja, name="gerenciarloja"),    
    path('exportarrelatorio/<str:relatorio>/', exportar_relatorio, name="exportar_relatorio"),

    path("password_change/", views.PasswordChangeView.as_view(), name="password_change"),
    path("password_change/done/", views.PasswordChangeDoneView.as_view(), name="password_change_done"),

    path("password_reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),


]
