# 📡 RSS Deck — Dashboard de Feeds em Tempo Real

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge">
  <img src="https://img.shields.io/badge/Flask-Framework-black?style=for-the-badge&logo=flask&logoColor=white" alt="Flask Badge">
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite Badge">
  <img src="https://img.shields.io/badge/CSS3-Vanilla-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3 Badge">
</p>

O **RSS Deck** é uma dashboard de notícias em tempo real inspirada no design clássico do *TweetDeck*. Ele permite acompanhar múltiplos canais de notícias (feeds RSS/Atom) de forma síncrona através de colunas verticais roláveis, organizadas em abas de categorias dinâmicas. O aplicativo conta com cache local SQLite persistente para busca histórica de notícias, alertas visuais neon e reordenação de colunas por arrastar e soltar (drag-and-drop).

---

## ✨ Principais Funcionalidades

- **🗂️ Categorias Dinâmicas e Customizadas**: Alterne facilmente entre abas organizadas (Ex: *Brasil, Mundo, Economia, Tecnologia, Guerras*) e crie novas categorias direto na interface.
- **🛠️ Gerenciador de Feeds RSS (CRUD)**: Cadastre novos feeds RSS em segundos, edite nomes/URLs, apague canais antigos ou alterne-os de categorias. O sistema executa uma varredura (*crawl*) automática e instantânea de novos feeds cadastrados.
- **🔄 Reordenação por Arrastar e Soltar (Drag & Drop)**: Organize visualmente suas colunas de feeds em tempo real arrastando-as de um lado para o outro. A nova ordem é salva e persistida automaticamente no banco de dados.
- **🚨 Tag Manager (Alertas Pulsantes)**: Cadastre palavras-chave e tags de monitoramento. Quando um termo cadastrado surge em uma notícia, o título ganha destaque neon vermelho pulsante e o card inteiro emite um brilho pulsante.
- **⏳ Viagem no Tempo (Time-Travel)**: Filtre o feed de notícias por data (dia específico no histórico) e faça buscas por palavra-chave instantâneas.
- **🧹 Filtros e Higienização Inteligente (UOL & Gerais)**: Impede a inserção de lixo, links duplicados ou cartões vazios (como placeholders comuns de notícias vazias do UOL). Garante que todos os cards tenham títulos e resumos reais.
- **⚡ Animações e Micro-Interações Premium**:
  - Efeito hover magnético e inclinável nos cards com reflexo de brilho varrendo a superfície (*shine sweep*).
  - Animação futurista de scan laser azul cobrindo a tela durante as atualizações manuais do feed.
  - Carregamento de colunas com efeito cascata (*staggered animations*).

---

## 🛠️ Stack Tecnológica

- **Backend**: Python 3, Flask, SQLite3, `feedparser`, `requests`, `urllib3`
- **Frontend**: HTML5 Semântico, CSS3 (Efeitos Glassmorphism, CSS Variables, Keyframes Avançados), Vanilla JavaScript (Drag and Drop nativo, Fetch API, DOM mutations)

---

## 📁 Estrutura do Banco de Dados

O banco SQLite local (`rss_deck.db`) utiliza uma estrutura relacional normalizada com integridade de chave estrangeira (`ON DELETE CASCADE`):

```mermaid
erDiagram
    categories {
        id INTEGER PK
        name TEXT UNIQUE
        display_order INTEGER
    }
    feeds {
        id INTEGER PK
        name TEXT
        url TEXT UNIQUE
        category TEXT
        column_index INTEGER
    }
    articles {
        id INTEGER PK
        feed_id INTEGER FK
        guid TEXT UNIQUE
        title TEXT
        description TEXT
        link TEXT
        pub_date TEXT
        fetched_date TEXT
    }
    tags {
        id INTEGER PK
        word TEXT UNIQUE
    }
    
    feeds }|--|| categories : "organizado em"
    articles }|--|| feeds : "pertence a"
```

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.10 ou superior instalado.

### Passo 1: Instale as Dependências
Clone o repositório e instale os pacotes necessários:
```bash
pip install -r requirements.txt
```

### Passo 2: Inicialize o Servidor
Execute o servidor Flask:
```bash
python app.py
```
O servidor inicializará o banco de dados `rss_deck.db`, povoará as categorias e feeds padrão se estiver vazio, e abrirá o serviço local.

### Passo 3: Acesse no Navegador
Abra a dashboard no seguinte link:
[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## 🧪 Rodando os Testes

Para validar a suíte integrada de testes unitários e rotas da API, execute:
```bash
pytest
```
A suíte valida:
- Integridade do esquema SQLite e sementes iniciais.
- Standardização de data/hora (RFC 822/ISO 8601).
- Rotas REST de feeds (criação, edição inline, exclusão, reordenação).
- Regras de filtros globais e purga de placeholders legados.

---

Desenvolvido com carinho e design premium. 📡
