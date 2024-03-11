
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy




# As views de Login e Logout foram sobrescritas para
# permitir uma melhor customização do processo de login
# e logout.


class LoginView(auth_views.LoginView):
    # Redirecionar caso o usuário já esteja logado
    redirect_authenticated_user = True

    # Página após o login
    next_page = reverse_lazy('post_list')


class LogoutView(auth_views.LogoutView):
    # Permitir deslogar com o get
    http_method_names = ["get", "post", "options"]

    # Página após o logout
    next_page = reverse_lazy('post_list')

    # Foward do get para o post
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


