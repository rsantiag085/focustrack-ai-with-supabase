# Changelog — FocusTrack AI

## [v1.2.0] — 2026-05-21

### Resumo

Adição de autenticação via Google OAuth, remoção de linguagem técnica/SRE da interface, versão visível no rodapé e otimizações de infraestrutura.

### Novidades

- **Login com Google**: botão "Continuar com Google" na tela de autenticação via Supabase OAuth
- **Versão visível**: número da versão exibido no rodapé do dashboard — facilita identificar atualizações
- **Interface genérica**: textos e placeholders reescritos para qualquer tipo de usuário, sem foco em SRE ou monitoramento
- **Nginx como reverse proxy**: frontend e backend unificados na porta 80; backend não exposto publicamente
- **Imagem Docker otimizada**: multi-stage build reduz a imagem de 500 MB para ~216 MB; dependências não utilizadas removidas

---

## [v1.1.0] — 2026-05-21

### Resumo

Esta versão consolida o frontend do FocusTrack AI com correções de segurança, refatorações de qualidade de código e melhorias de eficiência. Nenhuma funcionalidade nova foi adicionada — o foco foi estabilizar e proteger o que já existia.

---

## Segurança

### Vulnerabilidade XSS corrigida na timeline e no painel Jarbis

**Como funcionava antes:**
Os dados retornados pela API eram inseridos diretamente dentro de `innerHTML` via template literals. Qualquer texto salvo pelo usuário no campo `descricao`, ou retornado pela IA no campo `resumo_ia`, era interpretado pelo navegador como HTML bruto:

```js
// Antes — att.descricao e att.categoria injetados diretamente
item.innerHTML = `
    <h4>${att.categoria}</h4>
    <div class="timeline-desc">${att.descricao}</div>
`;

// Antes — resumo da IA injetado diretamente
document.getElementById('jarbis-insight').innerHTML =
    `<strong>Relatório Jarbis:</strong> <br> ${report.resumo_ia}`;
```

Um usuário mal-intencionado poderia salvar uma atividade com `descricao` contendo `<script>alert('XSS')</script>` e esse código seria executado no navegador de qualquer outro usuário que visualizasse a timeline. O mesmo vale para um atacante que comprometesse a resposta da IA ou fizesse uma chamada direta à API contornando o `<select>` de categorias.

**Como ficou depois:**
O HTML estrutural do item é gerado normalmente, mas os campos com dados do usuário são inseridos via `textContent`, que o navegador trata sempre como texto simples, nunca como markup:

```js
// Depois — estrutura HTML sem dados do usuário
item.innerHTML = `
    <h4></h4>
    <div class="timeline-desc"></div>
    ...
`;
// Dados do usuário inseridos com segurança
item.querySelector('h4').textContent = att.categoria;
item.querySelector('.timeline-desc').textContent = att.descricao;

// Depois — resumo da IA inserido com segurança
insightEl.innerHTML = '<strong>Relatório Jarbis:</strong><br>';
const text = document.createElement('span');
text.textContent = report.resumo_ia;
insightEl.appendChild(text);
```

**Ganho:** Elimina completamente o risco de Cross-Site Scripting (XSS) — uma das vulnerabilidades mais comuns e perigosas em aplicações web (OWASP Top 10).

---

## Qualidade de Código

### Tratamento de erros inconsistente nos wrappers de API

**Como funcionava antes:**
Cada função de API (`loadAtividades`, `saveAtividade`, `deleteAtividade`, `analisarDia`) tinha seu próprio bloco `try/catch` que logava o erro e — exceto `deleteAtividade` — o engolia silenciosamente, retornando `undefined` para o chamador sem nenhum aviso:

```js
// Antes — erro engolido, chamador recebe undefined sem saber
window.saveAtividade = async (atividadeData) => {
    try {
        const result = await window.apiFetch('/api/atividade', { method: 'POST', ... });
        return result;
    } catch (e) {
        console.error("Failed to save activity", e); // engolido aqui
    }
};

// handleSave não sabia que o save havia falhado
await window.saveAtividade(payload); // retorna undefined silenciosamente
await window.refreshDashboard();     // executa mesmo com falha
```

`deleteAtividade` era o único que re-lançava o erro, criando comportamento inconsistente sem justificativa.

**Como ficou depois:**
Os wrappers foram simplificados para delegar diretamente ao `apiFetch`, que já lança exceções em caso de falha. Os chamadores (`handleSave`, `handleDelete`, `handleAnalisar`) passaram a ter seus próprios blocos `try/catch`:

```js
// Depois — wrapper direto, erro propaga naturalmente
window.saveAtividade = (atividadeData) => window.apiFetch('/api/atividade', {
    method: 'POST',
    body: JSON.stringify(atividadeData)
});

// handleSave agora sabe quando o save falhou
async function handleSave() {
    try {
        await window.saveAtividade(payload);
        await window.refreshDashboard();
    } catch (e) {
        console.error("Failed to save activity:", e);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}
```

**Ganho:** Falhas reais são agora visíveis ao chamador. A lógica pós-salvamento (`refreshDashboard`, limpar formulário) não é mais executada quando o save falha.

---

### Botões travados permanentemente em caso de erro

**Como funcionava antes:**
`handleSave` e `handleAnalisar` desabilitavam o botão e trocavam seu texto para indicar carregamento, mas restauravam o estado fora de um bloco `finally`. Se a chamada assíncrona lançasse uma exceção, o código de restauração nunca era executado e o botão ficava permanentemente travado na tela:

```js
// Antes — sem finally: botão trava se a chamada falhar
async function handleSave() {
    btn.innerText = "Salvando...";
    btn.disabled = true;

    await window.saveAtividade(payload); // se lançar, as linhas abaixo nunca executam
    await window.refreshDashboard();

    btn.innerText = originalText; // nunca alcançado em caso de erro
    btn.disabled = false;         // nunca alcançado em caso de erro
}
```

**Como ficou depois:**
A restauração do botão foi movida para o bloco `finally`, que executa independentemente de sucesso ou falha:

```js
// Depois — finally garante que o botão sempre volta ao estado original
async function handleSave() {
    btn.innerText = "Salvando...";
    btn.disabled = true;
    try {
        await window.saveAtividade(payload);
        await window.refreshDashboard();
    } catch (e) {
        console.error("Failed to save activity:", e);
    } finally {
        btn.innerText = originalText; // sempre executado
        btn.disabled = false;         // sempre executado
    }
}
```

**Ganho:** O usuário nunca fica com a interface bloqueada após um erro de rede ou de servidor.

---

### Código duplicado em `doLogin` e `doSignUp`

**Como funcionava antes:**
As duas funções liam os campos de email e senha do DOM de forma idêntica e duplicavam o bloco de exibição de erro. Além disso, `doLogin` não resetava a cor do elemento de erro, o que causava um bug visual: após uma mensagem de sucesso de cadastro (em verde), se o usuário tentasse logar e falhasse, a mensagem de erro aparecia em verde em vez de vermelho:

```js
// Antes — leitura de DOM duplicada nas duas funções
async function doLogin() {
    // ... sem reset de cor
    try {
        await window.handleLogin(
            document.getElementById('auth-email').value,   // duplicado
            document.getElementById('auth-password').value // duplicado
        );
    } catch (e) {
        errEl.innerText = e.message;    // duplicado
        errEl.style.display = 'block';  // duplicado
        // cor nunca resetada — bug visual
    }
}
```

**Como ficou depois:**
Extraída a função `getAuthInput()` para eliminar a duplicação. Ambas as funções agora resetam a cor explicitamente:

```js
// Depois — leitura de credenciais centralizada
function getAuthInput() {
    return {
        email: document.getElementById('auth-email').value,
        password: document.getElementById('auth-password').value
    };
}

async function doLogin() {
    const { email, password } = getAuthInput();
    try {
        await window.handleLogin(email, password);
    } catch (e) {
        errEl.style.color = 'var(--danger)'; // sempre correto
        errEl.innerText = e.message;
        errEl.style.display = 'block';
    }
}
```

**Ganho:** Elimina duplicação de lógica de DOM e corrige o bug visual de cor na mensagem de erro de autenticação.

---

### Comentários desnecessários removidos

**Como funcionava antes:**
O código continha 13 comentários que descreviam exatamente o que o código já dizia por si só, além de um separador decorativo (`// ---...`), um JSDoc para `apiFetch` sem informação adicional, e um comentário com informação errada ("mapped from .env" quando as credenciais eram literais hardcoded):

```js
// Initialize the Supabase client first with actual credentials mapped from .env
// Attach the client globally immediately
// User is logged in
// No user session
// Explicitly attach Authentication Handlers to the window object
// We clear timelines out visually right away
// Global function called seamlessly from app.js upon detecting a valid session via onAuthStateChange
// Setup base states once the window naturally loads
// ...e outros
```

**Como ficou depois:** Todos removidos. O código restante é autoexplicativo.

**Ganho:** Código mais limpo e fácil de ler. Remove informações desatualizadas que poderiam confundir futuros mantenedores.

---

## Eficiência

### Constante `BACKEND_URL` declarada dentro da função a cada chamada

**Como funcionava antes:**
A URL base do backend era declarada como `const` dentro do corpo de `apiFetch`, sendo realocada em memória a cada chamada à API:

```js
// Antes — redeclarada a cada chamada
window.apiFetch = async (endpoint, options = {}) => {
    // ...
    try {
        const backendUrl = 'http://localhost:8000'; // recriada sempre
        const response = await fetch(`${backendUrl}${endpoint}`, config);
    }
};
```

**Como ficou depois:**
Movida para o escopo do módulo como constante única:

```js
// Depois — declarada uma única vez
const BACKEND_URL = 'http://localhost:8000';

window.apiFetch = async (endpoint, options = {}) => {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, { ...options, headers });
};
```

**Ganho:** Elimina alocação desnecessária a cada chamada de API. Centraliza a configuração do backend em um único lugar, facilitando mudanças de ambiente.

---

### `onAuthStateChange` disparava `refreshDashboard` em todo evento de autenticação

**Como funcionava antes:**
O listener de autenticação do Supabase chamava `refreshDashboard()` sempre que `session` existia — independentemente do tipo de evento. O Supabase dispara esse callback para vários eventos: `INITIAL_SESSION`, `SIGNED_IN`, `TOKEN_REFRESHED`, `USER_UPDATED`, entre outros. Isso causava uma nova requisição completa ao servidor toda vez que o token era renovado silenciosamente em segundo plano (a cada ~60 minutos de uso):

```js
// Antes — refreshDashboard chamado em QUALQUER evento com sessão ativa
supabase.auth.onAuthStateChange(async (event, session) => {
    if (session) {
        // ...
        if (typeof window.refreshDashboard === 'function') {
            window.refreshDashboard(); // dispara também em TOKEN_REFRESHED, USER_UPDATED...
        }
    }
});
```

**Como ficou depois:**
O refresh do dashboard é restrito apenas aos eventos relevantes de início de sessão:

```js
// Depois — refresh apenas quando necessário
supabase.auth.onAuthStateChange(async (event, session) => {
    if (session) {
        // ...
        if ((event === 'SIGNED_IN' || event === 'INITIAL_SESSION') &&
            typeof window.refreshDashboard === 'function') {
            window.refreshDashboard();
        }
    }
});
```

**Ganho:** Elimina chamadas desnecessárias à API em renovações silenciosas de token, reduzindo carga no servidor e no banco de dados.

---

### Métricas atualizadas antes do loop de acumulação

**Como funcionava antes:**
`metric-count` era atualizado no DOM antes do loop que processava as atividades. Se o loop lançasse uma exceção, o contador já teria sido atualizado na tela com um valor potencialmente inconsistente com o restante da UI. As outras duas métricas (`metric-focus`, `metric-hours`) eram atualizadas após o loop em um bloco `if/else` redundante:

```js
// Antes — count atualizado antes do loop; focus/hours duplicados no if/else
document.getElementById('metric-count').innerText = atividades.length; // antes do loop

atividades.forEach(att => { /* ... acumula totalFocus e totalMs ... */ });

if (atividades.length > 0) {
    document.getElementById('metric-focus').innerText = (totalFocus / atividades.length).toFixed(1);
    document.getElementById('metric-hours').innerText = (totalMs / 3600000).toFixed(1);
} else {
    document.getElementById('metric-focus').innerText = "0.0"; // duplica os getElementById
    document.getElementById('metric-hours').innerText = "0.0";
}
```

**Como ficou depois:**
Todas as três métricas são atualizadas juntas após o loop, e o `if/else` foi substituído por expressões ternárias:

```js
// Depois — todas as métricas atualizadas juntas após o loop
atividades.forEach(att => { /* ... acumula totalFocus e totalMs ... */ });

document.getElementById('metric-count').innerText = atividades.length;
document.getElementById('metric-focus').innerText =
    atividades.length > 0 ? (totalFocus / atividades.length).toFixed(1) : "0.0";
document.getElementById('metric-hours').innerText =
    atividades.length > 0 ? (totalMs / 3600000).toFixed(1) : "0.0";
```

**Ganho:** Métricas sempre atualizadas em conjunto e de forma consistente. Adicionar uma quarta métrica no futuro requer apenas uma linha, não três.

---

## Arquivos Alterados

| Arquivo | Tipo de alteração |
|---|---|
| `frontend/app.js` | Segurança, qualidade, eficiência |
| `frontend/index.html` | Segurança, qualidade, eficiência |
