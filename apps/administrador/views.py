from django.shortcuts import get_object_or_404, redirect, render, get_list_or_404
from django.contrib.auth.decorators import login_required
from apps.reserva.models import Confirmacao, Registro, ReservasFinalizadas
from .models import Chamado, NivelUsuario, Espacos
from datetime import datetime, date, timedelta
from django.contrib.auth.models import User
from .validar.validate import valida_email
from django.contrib import messages, auth
from core.settings import BASE_DIR
from apps.reserva.utils import *
import os
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template

#========================LOGIN ADM=======================
def login(request):
    """PAGINA DE LOGIN DO ADMINISTRADOR"""
    if request.method ==  'POST':
        email = request.POST['email']
        senha = request.POST['senha']
        #SE O EMAIL FOR VALIDO E CONSTAR NO BANCO
        if User.objects.filter(email = email).exists():
            nome = User.objects.filter(email = email).values_list('username',flat=True).get()
            user = auth.authenticate(request, username = nome, password = senha)
            if user is not None:
                auth.login(request, user)
                return redirect('administrador')
        messages.error(request, 'E-mail ou Senha Inválidos')
    return render(request,'login.html')

def logout(request):
    """REALIZAÇÂO DE LOGOUT DO USUARIO"""
    auth.logout(request)
    return redirect('/adm/login')
#========================END LOGIN ADM=======================


#========================ADMINISTRADOR=======================
@login_required(login_url='/adm/login')
def administrador(request):
    """PAGINA DE ADMINISTRADOR"""
    usuario = request.user.id
    conteudo = {'nivel': get_object_or_404(NivelUsuario, usuario=usuario)}
    return render(request, 'administrador.html', conteudo)

@login_required(login_url='/adm/login')
def gerenciar_usuario(request):
    """Página de Listagem de Usuários Administradores do Sistema"""
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        users = {'users': User.objects.all()}
        return render(request, 'administrador/gerenciar_usuario.html', users)
    else:
        return redirect('administrador')

@login_required(login_url='/adm/login')
def adicionar_adm(request):
    """PAGINA DE REGISTRO DE NOVO ADMINISTRADOR"""
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    print(nivel.status)
    if nivel.status == 'TOP':
        if request.method == 'POST':
            nome = request.POST['nome_usuario']
            email = request.POST['email']
            senha = request.POST['senha']
            tipo = request.POST['nivel']
            if valida_email(email):
                if not User.objects.filter(username=nome, email=email):
                    user =User.objects.create_user(username = nome, email = email,  password = senha)
                    user.save()
                    user_id = User.objects.get(email = email)
                    user_n = get_object_or_404(User, pk= user_id.id)
                    nivel = NivelUsuario.objects.create(usuario = user_n, status= tipo)
                    nivel.save()
                    messages.success(request, 'Usuário criado com sucesso')
                    return redirect('gerenciar_usuario')
                else:
                    messages.error(request, 'Usuário já existe')
                    return redirect('adicionar_adm')
            else:
                messages.error(request, 'Usuário invalido')
                return redirect('adicionar_adm')
        return render(request, 'administrador/adicionar_adm.html')
    else:
        return redirect('administrador')

@login_required(login_url='/adm/login')
def editar_adm(request, usuario_id):
    """Página de Edição de Usuário"""
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        usuario =get_object_or_404(User, pk=usuario_id)
        if request.method == 'POST':
            nome = request.POST['nome']
            email = request.POST['email']
            tipo = request.POST['nivel']
            usuario.username = nome
            usuario.email = email
            usuario.save()
            user_nivel = get_object_or_404(NivelUsuario, usuario=usuario)
            user_nivel.status = tipo
            user_nivel.save()

            return redirect('gerenciar_usuario')
        usuarios = get_object_or_404(User, pk=usuario_id)
        return render(request, 'administrador/editar_adm.html', {'usuario' : usuarios})
    else:
        return redirect('administrador')

@login_required(login_url='adm/login')
def deletar_adm(request,usuario_id):
    """Função Que Deleta o Usuario Selecionado"""
    usuario_on = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario_on)
    if nivel.status == 'TOP':
        usuario = get_object_or_404(User,pk=usuario_id)
        if not usuario_on == usuario.id: 
            usuario.delete()
            messages.success(request, "Usuário deletado com sucesso")
            return redirect('gerenciar_usuario')
        messages.error(request, 'Você não apagar o usuário que está logado')
        return redirect('gerenciar_usuario')
    else:
        return redirect('administrador')

@login_required(login_url='adm/login')
def buscar_adm(request):
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        if 'buscar' in request.POST:
            nome_buscado = request.POST['buscar']
            print(nome_buscado)
            if nome_buscado.strip() != "":
                usuario = User.objects.filter(username=nome_buscado)
                user = {
                    'user' : usuario,
                } 
                return render(request,'busca/busca_adm.html',user)
        return redirect('gerenciar_usuario')
    else:
        return redirect('administrador')
#========================END ADMINISTRADOR===================


#===================GERENCIAMENTO DE RESERVA=================
@login_required(login_url='/adm/login')
def gerenciar_reserva(request):
    """Página de Listagem de Reservas Confirmadas"""
    registros = {'registros': Registro.objects.all()}
    return render(request, 'reserva/gerenciar_reserva.html', registros)

@login_required(login_url='/adm/login')
def cancelar_reserva(request, reserva_id):
    """Cancelar Reserva"""
    reserva = Registro.objects.get(id=reserva_id)
    motivo = request.POST['texto-cancelar']
    conteudo = {'espacos':reserva.espacos, 'agente':reserva.agente, 'data_reserva':reserva.data_reserva, 'hora_inicio':reserva.hora_inicio, 'hora_fim':reserva.hora_fim, 'motivo':motivo}
    email_html('emails/reserva_cancelada.html', 'Cancelamento da Reserva', ['suportesigen@gmail.com', reserva.email], conteudo)
    reserva.delete()
    return redirect('/adm/gerenciar_reserva/')

@login_required(login_url='/adm/login')
def check_in(request):
    """PAGINA DE CHECK-IN/OUT"""
    if 'buscar' in request.POST:
        nome_buscado = request.POST['buscar']
        print(nome_buscado)
        if nome_buscado.strip() != "":
            empresa = Registro.objects.filter(empresa=nome_buscado)
            conteudo = {'casos' : Confirmacao.objects.filter(registro__in=empresa,check_in=False)}
            return render(request,'checkin/check_in.html',conteudo)

    conteudo = {"casos": Confirmacao.objects.filter(check_in=False).all(),
    }
    return render(request, 'checkin/check_in.html',conteudo)

@login_required(login_url='/adm/login')
def realizar_check_in(request,id):
    """REALIZAR CHECK IN DAS RESERVAS"""
    checando = get_object_or_404(Confirmacao,pk=id)
    data_atual = datetime.now() + timedelta(minutes=30)
    tmp_atraso = data_atual.time()
    data_cadastrada = datetime.strptime(str(checando.registro.hora_inicio),"%H:%M:%S")
    hr_reserva = data_cadastrada.time()
    if checando.registro.data_reserva == date.today() and hr_reserva <= tmp_atraso:
        if checando.check_in == False:
            checando.check_in = True
            checando.horario_checkin = datetime.now().strftime('%H:%M:%S')
        checando.save()
        messages.success(request, 'Check-in realizado com sucesso')
    else:
        messages.error(request, 'Check-in não realizado, verifique a data')
    return redirect('check_in')

def check_out(request):
    """PAGINA DE CHECK-IN/OUT"""
    if 'buscar' in request.POST:
        nome_buscado = request.POST['buscar']
        print(nome_buscado)
        if nome_buscado.strip() != "":
            empresa = Registro.objects.filter(empresa=nome_buscado)
            conteudo = {'casos' : Confirmacao.objects.filter(registro__in=empresa,check_in=True,check_out=False)}
            return render(request,'checkin/check_out.html',conteudo)
    conteudo = {"casos": Confirmacao.objects.filter(check_in= True,check_out= False).all(),
    }
    return render(request, 'checkin/check_out.html',conteudo)

def realizar_check_out(request, id):
    """REALIZAR CHECK IN DAS RESERVAS"""
    checando = get_object_or_404(Confirmacao, pk=id)
    if checando.registro.data_reserva == date.today():
        if checando.check_in == True and checando.check_out == False:
            quantidade = request.POST['quantidade']
            checando.qtd_participantes = quantidade
            checando.horario_checkot = datetime.now().strftime('%H:%M:%S')
            checando.check_out = True
        checando.save()
        if checando.check_in == True and checando.check_out == True:
            empresa = checando.registro.empresa
            agente = checando.registro.agente
            data = checando.registro.data_reserva
            hora_inicio = checando.registro.hora_inicio
            hora_fim = checando.registro.hora_fim
            espaco = checando.registro.espacos
            registro= checando.registro
            check_in = checando.horario_checkin
            check_out = checando.horario_checkot
            quantidade_de_pessoas = checando.qtd_participantes

            reserva = ReservasFinalizadas.objects.create(
                empresa = empresa,
                agente = agente,
                data = data,
                hora_inicio = hora_inicio,
                hora_fim = hora_fim,
                espaco = espaco,
                registro= registro,
                check_in = check_in,
                check_out = check_out,
                quantidade_de_pessoas = quantidade_de_pessoas,
                )
            reserva.save()
    return redirect('check_out')

@login_required(login_url='adm/login')
def buscar_reserva(request):
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        if 'buscar' in request.POST:
            nome_buscado = request.POST['buscar']
            print(nome_buscado)
            if nome_buscado.strip() != "":
                reserva = Registro.objects.filter(empresa=nome_buscado)
                empresas = {
                    'registros' : reserva,
                } 
                return render(request,'busca/busca_reserva.html',empresas)
        return redirect('gerenciar_reserva')
    else:
        return redirect('administrador')
#=================END GERENCIAMENTO DE RESERVA=================


#================RELATORIOS DE USO DOS ESPAÇOS=================
@login_required(login_url='/adm/login')
def gerenciar_relatorios(request):
    """RELATORIOS DE USO DOS ESPAÇOS"""
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        espacos = {'espacos': Espacos.objects.all()}
        return render(request, 'relatorios/gerenciar_relatorios.html', espacos)
    else:
        return redirect('administrador')

@login_required(login_url='/adm/login')
def relatorio(request,espaco_id, opc='n'):
    """GERAR RELATÓRIO DE UM ESPAÇO ESPECIFICO"""
    usuario = request.user.id
    espaco = Espacos.objects.get(pk=espaco_id)
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        if opc == 'n':
            registros = ReservasFinalizadas.objects.filter(espaco=espaco_id)
        elif opc == 'd':
            registros = ReservasFinalizadas.objects.filter(espaco=espaco_id).filter(data__gt= datetime.now())
        elif opc == 's':
            registros = ReservasFinalizadas.objects.filter(espaco=espaco_id).filter(data__gt= datetime.now()-timedelta(days=7))
        elif opc == 'm':
            registros = ReservasFinalizadas.objects.filter(espaco=espaco_id).filter(data__gt= datetime.now()-timedelta(days=30))
        
        context = {
        'registros': registros,
        'espaco': espaco,
            #'reservas_finalizadas': reservas_finalizadas,
        }

        return render(request, 'relatorios/relatorio.html', context)
    else:
        return redirect('administrador')
@login_required(login_url='/adm/login')
def render_pdf_view(request, registro_id):

    registro = get_object_or_404(ReservasFinalizadas, id=registro_id)
    print(registro)  
    template_path = 'pdf1.html'
    context = {'registro': registro}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    #if dowaload:
    #response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # if display:
    response['Content-Disposition'] = 'filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>',context)
    return response
    
    
#==============END RELATORIOS DE USO DOS ESPAÇOS===============


#===================GERENCIAMENTO DE ESPAÇOS===================
@login_required(login_url='/adm/login')
def gerenciar_espacos(request):
    """PAGINA DE GERENCIAMENTO DE ESPAÇOS"""
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        return render(request, 'espacos/gerenciar_espacos.html', {'espacos': Espacos.objects.all()})
    else:
        return redirect('administrador')

@login_required(login_url='/adm/login')
def remover_espaco_id(request, espaco_id):
    """REMOVER ESPAÇO ESPECIFICO"""
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        espaco = get_object_or_404(Espacos, pk=espaco_id)
        os.remove(os.path.join(BASE_DIR, espaco.imagem1.path))
        espaco.delete()
        return redirect('/adm/gerenciar_espacos/')
    else:
        return redirect('/adm/gerenciar_espacos/')

@login_required(login_url='/adm/login')
def editar_espaco_id(request, espaco_id):
    """EDITAR ESPAÇO ESPECIFICO"""
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        if request.method == 'POST':
            espaco = Espacos.objects.get(id=espaco_id)
            
            nome = request.POST['input-nome']
            descricao = request.POST['input-descricao']
            try:
                imagem = request.FILES['input-imagem']
                os.remove(os.path.join(BASE_DIR, espaco.imagem1.path))
                espaco.imagem1 = imagem
            except:
                pass
            capacidade = request.POST['input-capacidade']

            espaco.nome = nome
            espaco.descricao = descricao
            espaco.capacidade = capacidade
            espaco.save()
            return redirect('/adm/gerenciar_espacos/')
    else:
        return redirect('administrador')

@login_required(login_url='/adm/login')
def adicionar_espaco(request):
    """ADCICIONAR ESPAÇO ESPECIFICO"""
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        if request.method == 'POST':
            nome = request.POST['input-nome']
            descricao = request.POST['input-descricao']
            imagem1 = request.FILES['input-imagem']
            capacidade = request.POST['input-capacidade']
            espaco = Espacos.objects.create(nome=nome, descricao=descricao, imagem1=imagem1, capacidade=capacidade)
            return redirect('/adm/gerenciar_espacos/')
#==================END GERENCIAMENTO DE ESPAÇOS=================


#=======================ABERTURA DE CHAMADO=====================
@login_required(login_url='/adm/login')
def gerenciar_chamados(request):
    """ADCICIONAR ESPAÇO ESPECIFICO"""
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        if request.method == 'POST':
            filtro = request.POST['filtro']          
            if filtro == 'aberto':
                chamados = { 'chamados': Chamado.objects.order_by('data').filter(status='abt')}              
            elif filtro == 'andamento':
                chamados = { 'chamados': Chamado.objects.order_by('data').filter(status='and')}
            elif filtro == 'concluido':
                chamados = { 'chamados': Chamado.objects.order_by('data').filter(status='ccl')}
            else:
                chamados = { 'chamados': Chamado.objects.order_by('data').all()}
        else:
            chamados = { 'chamados': Chamado.objects.order_by('data').all()}
        return render(request, 'chamados/gerenciar_chamados.html',chamados)
    else:
        return redirect('administrador')

@login_required(login_url='/adm/login')
def atualizar_chamado(request, chamado_id):
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        chamado = get_object_or_404(Chamado, pk=chamado_id)
        if chamado.status == 'abt':
            chamado.status = 'and'
            chamado.save()
            messages.success(request, 'Status Atualizado')
            return redirect('gerenciar_chamados')
    else:
        return redirect('administrador')

@login_required(login_url='/adm/login')
def concluir_chamado(request, chamado_id):
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        chamado = get_object_or_404(Chamado, pk=chamado_id)
        if chamado.status == 'and':
            if request.method == 'POST':
                atualizacao = request.POST['atualizacao']
                chamado.atualizacao = atualizacao
                chamado.data_conclusao = date.today()
                chamado.status = 'ccl'
                chamado.save()

                solicitante = chamado.solicitante
                email= chamado.email_solicitante
                data =  chamado.data
                ambiente = chamado.ambiente       
                objeto = chamado.objeto
                descricao = chamado.descricao
                atualizacao = chamado.atualizacao
                data_conclusao = chamado.data_conclusao


                conteudo = {
                'nome_solicitante':solicitante,
                'email_solicitante':email, 
                'data':data, 
                'ambiente':ambiente, 
                'objeto':objeto, 
                'descricao':descricao,
                'atualizacao': atualizacao,
                'data_conclusao': data_conclusao,
                }
                email_html('emails/conclusao_chamado.html', 'envio de chamado',['suportesigen@gmail.com',email], conteudo)
                messages.success(request, 'Chamado Finalizado')
                return redirect('gerenciar_chamados')

    else:
        return redirect('administrador')

@login_required(login_url='/adm/login')
def detalhes_chamado(request, chamado_id):
    usuario = request.user.id
    nivel = get_object_or_404(NivelUsuario, usuario=usuario)
    if nivel.status == 'TOP':
        chamado ={'chamado': get_object_or_404(Chamado, pk=chamado_id)}
        return render(request,'chamados/detalhes.html',chamado)
    else:
        return redirect('administrador')


# @login_required(login_url='adm/login')
# def buscar_chamado(request):
#     usuario = request.user.id
#     nivel = get_object_or_404(NivelUsuario, usuario=usuario)
#     if nivel.status == 'TOP':
#         if 'buscar' in request.POST:
#             nome_buscado = request.POST['buscar']
#             print(nome_buscado)
#             if nome_buscado.strip() != "":
#                 result = Chamado.objects.filter(solicitante=nome_buscado)
#                 chamados = {
#                     'chamados' : result,
#                 } 
#                 return render(request,'busca/busca_chamado.html',chamados)
#         return redirect('gerenciar_chamados')
#     else:
#         return redirect('administrador')


@login_required(login_url='/adm/login')
def abrir_chamado(request):
    espacos = Espacos.objects.all()
    espacos = {"espacos":espacos,}
    if request.method == "POST": 
        solicitante = request.POST["solicitante"]
        email = request.POST["email_solicitante"]
        ambiente = request.POST["ambiente"]
        ambiente2 = get_object_or_404(Espacos, pk=ambiente)
        objeto = request.POST["objeto"]
        descricao = request.POST["descricao"]
        if valida_email(email):
            chamado = Chamado.objects.create(solicitante=solicitante, email_solicitante=email, ambiente=ambiente2, objeto=objeto, descricao=descricao)
            chamado.save()
            conteudo = {'nome_solicitante':solicitante,'email_solicitante':email, 'ambiente':ambiente2, 'data':chamado.data, 'objeto':objeto, 'descricao':descricao}
            email_html('emails/email_chamado.html', 'envio de chamado', ['suportesigen@gmail.com'], conteudo)
            return redirect('/adm/gerenciar_chamados/')
        else:
            messages.error(request,'Email Inválido, Tente Novamente')
            return redirect('gerenciar_chamados')
    return render(request,'chamados/chamados.html', espacos)
#=====================END ABERTURA DE CHAMADO====================
