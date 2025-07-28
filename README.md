# Backend do Sistema de Cardápio Digital

Este é o backend do sistema de cardápio digital, desenvolvido com Django e Django REST Framework.

## Requisitos

- Python 3.8+
- pip
- virtualenv (recomendado)

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o banco de dados:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Crie um superusuário:
```bash
python manage.py createsuperuser
```

6. Execute o servidor:
```bash
python manage.py runserver
```

## Estrutura do Projeto

- `accounts/`: Gerenciamento de usuários e restaurantes
- `products/`: Gerenciamento de produtos, categorias e ingredientes
- `orders/`: Gerenciamento de pedidos
- `dashboard/`: Estatísticas e métricas
- `settings/`: Configurações do restaurante

## Endpoints da API

### Autenticação
- `POST /api/token/`: Obter token JWT
- `POST /api/token/refresh/`: Renovar token JWT

### Contas
- `POST /api/accounts/users/login/`: Login de usuário
- `GET /api/accounts/restaurants/me/`: Informações do restaurante atual

### Produtos
- `GET /api/products/categories/`: Listar categorias
- `POST /api/products/categories/`: Criar categoria
- `GET /api/products/products/`: Listar produtos
- `POST /api/products/products/`: Criar produto
- `GET /api/products/ingredients/`: Listar ingredientes
- `POST /api/products/ingredients/`: Criar ingrediente

### Pedidos
- `GET /api/orders/orders/`: Listar pedidos
- `POST /api/orders/orders/`: Criar pedido
- `GET /api/orders/orders/pending/`: Pedidos pendentes
- `GET /api/orders/orders/preparing/`: Pedidos em preparo
- `GET /api/orders/orders/ready/`: Pedidos prontos
- `GET /api/orders/orders/today/`: Pedidos do dia

### Dashboard
- `GET /api/dashboard/summary/`: Resumo do dashboard
- `GET /api/dashboard/daily_stats/`: Estatísticas diárias
- `GET /api/dashboard/product_stats/`: Estatísticas de produtos
- `GET /api/dashboard/category_stats/`: Estatísticas de categorias

### Configurações
- `GET /api/settings/settings/me/`: Configurações do restaurante
- `PUT /api/settings/settings/me/`: Atualizar configurações
- `GET /api/settings/business-hours/current/`: Horários de funcionamento
- `POST /api/settings/business-hours/bulk_update/`: Atualizar horários

## Autenticação

O sistema usa JWT (JSON Web Tokens) para autenticação. Para acessar os endpoints protegidos, inclua o token no header da requisição:

```
Authorization: Bearer <seu_token>
```

## Desenvolvimento

1. Ative o ambiente virtual
2. Execute o servidor de desenvolvimento:
```bash
python manage.py runserver
```

3. Acesse a API em `http://localhost:8000/api/`
4. Acesse o admin em `http://localhost:8000/admin/`

## Produção

Para ambiente de produção, certifique-se de:

1. Configurar `DEBUG = False` em settings.py
2. Definir uma `SECRET_KEY` segura
3. Configurar `ALLOWED_HOSTS`
4. Configurar um banco de dados adequado (PostgreSQL recomendado)
5. Configurar um servidor web (Nginx + Gunicorn recomendado)
6. Configurar CORS adequadamente
7. Configurar SSL/HTTPS 