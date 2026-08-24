# Sentinela DIO-ES

Monitora o Diário Oficial do Estado do Espírito Santo (Sistema IOES) e envia
notificação quando um termo configurado é publicado.

Feito para quem precisa acompanhar o próprio nome no Diário — servidores
públicos, profissionais liberais, advogados — sem depender de folhear edições
de 80 páginas todos os dias.

## Por que existe

O portal do DIO/ES oferece uma "Pesquisa Agendada" oficial por e-mail. Quando
ela não está disponível, resta acompanhar manualmente. Este add-on automatiza
isso e, mais importante, **avisa quando ele próprio para de funcionar** — um
monitor silencioso é pior que monitor nenhum, porque gera falsa segurança.

## Como funciona

A cada horário configurado, consulta a API do portal para cada um dos últimos
`dias_retroativos` dias:

```
/apifront/portal/edicoes/edicoes_from_data/AAAA-MM-DD.json?subtheme=
```

A resposta traz, para cada edição daquela data, o ID interno, o número
publicado e a quantidade de páginas. As edições ainda não processadas são
baixadas inteiras num único arquivo, o texto é extraído, normalizado e
comparado com as expressões regulares configuradas.

### Dois números diferentes

O portal exibe o número **publicado** (ex.: 26789, o do cabeçalho impresso),
mas todas as URLs internas usam um **ID** distinto (ex.: 11389). Confundir os
dois é o erro mais provável ao mexer neste código. O add-on resolve pela data,
então o usuário não precisa informar nenhum dos dois.

Os IDs são globais no sistema IOES, que hospeda também diários municipais —
edições consecutivas do Diário do Estado podem estar a mais de dez IDs de
distância. Por isso a busca é por data e filtrada por `tipo_edicao_id`.

## Configuração

| Opção | Padrão | Descrição |
|---|---|---|
| `termos` | — | Expressões regulares procuradas |
| `dias_retroativos` | 7 | Janela de dias consultada a cada execução |
| `tipo_edicao_id` | 1 | 1 = Diário Oficial do Espírito Santo |
| `usar_download_completo` | true | Baixa a edição inteira; se falhar, cai para página a página |
| `incluir_trecho` | false | Inclui o texto ao redor da ocorrência na notificação |
| `incluir_link` | true | Anexa o link do relatório à notificação |
| `notify_service` | — | Serviço clássico, ex.: `mobile_app_meu_iphone` |
| `notify_entity` | — | Entidade notify, ex.: `notify.meu_celular` |
| `horarios` | 07/13/19 | Horários das varreduras |
| `pausa_segundos` | 0.4 | Intervalo entre requisições ao portal |

Preencha **os dois** campos de notificação. O serviço clássico é tentado
primeiro porque é o único que aceita `data` — sem ele a notificação não leva
link nem prioridade, e tocar nela só abre o dashboard padrão do app.
`notify.send_message` (a entidade) entra apenas como reserva.

O nome do serviço clássico segue o **nome do dispositivo** no registro do Home
Assistant, não o `entity_id`. Se o aparelho foi renomeado, os dois divergem:
a entidade pode continuar `notify.iphone_17_pro` enquanto o serviço já é
`mobile_app_iphone_tompson`. Nome errado responde HTTP 400 seco. Confira em
**Ferramentas de desenvolvedor → Ações**, procurando por `notify.mobile_app_`.
Se errar, o add-on lista no log os serviços que existem.

### Escrevendo os termos

São expressões regulares aplicadas ao texto **já normalizado**: sem acento,
tudo em maiúsculas, espaços colapsados, hifenização de fim de linha desfeita.
Escreva sempre em maiúsculas e sem acento.

Use aspas simples no YAML para não precisar duplicar as barras invertidas:

```yaml
termos:
  - '\bSOBRENOME\b'
  - '\b1234567\b'
  - 'NOME\s+COMPOSTO'
```

- `\b` marca borda de palavra. Sem ele, `1234567` casaria dentro de `12345678`.
- `\s+` no lugar de cada espaço: o Diário é diagramado em colunas estreitas e
  parte nomes no fim da linha.
- **Sobrenome raro sozinho costuma ser gatilho melhor que nome completo**, que
  aparece abreviado ou invertido. Falso positivo custa dez segundos de leitura;
  falso negativo custa um prazo.
- **Matrícula funcional é o gatilho mais confiável** em portarias.

Mudar a lista de termos faz o add-on reprocessar a janela retroativa inteira,
de modo que um termo acrescentado hoje seja procurado também nas edições
recentes.

## A página do relatório

A cada varredura com achados, o add-on grava
`<config>/www/sentinela_dioes/ultimo.html` e manda esse endereço na
notificação (`/local/sentinela_dioes/ultimo.html`). Tocar no alerta abre a
página dentro do app, com todas as ocorrências agrupadas por edição: termo,
página, trecho ao redor com o termo destacado, link para a página no portal e
link para o PDF da edição. Cada varredura também deixa uma cópia datada; as 30
mais recentes são mantidas.

Isso exige `homeassistant_config:rw` no mapeamento do add-on — já está em
`config.yaml`, mas uma instalação antiga precisa ser atualizada para receber a
permissão.

> A pasta `www` é servida em `/local/` **sem autenticação**: quem alcançar o
> endereço do Home Assistant e souber o caminho lê o relatório. O conteúdo é
> recorte de publicação oficial, já pública, mas revela quais nomes você
> monitora. Se o Home Assistant estiver exposto à internet, considere isso.

## O que ele faz para não falhar calado

- Repete requisição com erro de rede; HTML com HTTP 200 (recurso inexistente)
  é reconhecido de imediato, sem insistir.
- Janela retroativa: se o Home Assistant ficar dias fora do ar, recupera o
  atrasado sozinho ao voltar.
- Compara as páginas lidas com as anunciadas pela API e avisa se faltar.
- Avisa se metade das páginas vier sem camada de texto — o dia em que o portal
  passar a publicar imagem escaneada.
- Avisa se o portal não devolver edição nenhuma na janela inteira: quase sempre
  significa que a API mudou, não que o Diário parou.
- Notifica a própria exceção se algo estourar.

## Limitação conhecida

Matéria publicada como imagem escaneada não é encontrada, porque não há texto a
extrair. Nas edições testadas isso ocorre apenas na capa, que não traz matéria.
Se passar a ocorrer no miolo, a solução é acrescentar OCR nas páginas sem
camada de texto.

## Onde ficam os dados

- Edições já processadas: `/data/estado.json`
- PDF das edições com ocorrência: `share/sentinela_dioes/achados/`
- Relatório HTML: `config/www/sentinela_dioes/` (`/local/sentinela_dioes/`)
- Log: aba **Registro** do add-on

## Adaptação para outros estados

O sistema IOES é usado por diários oficiais de outras unidades da federação. Em
tese basta trocar o domínio em `sentinela.py` e ajustar `tipo_edicao_id`. Não
testado.

## Aviso

Este add-on não tem vínculo com o Governo do Estado do Espírito Santo nem com a
Imprensa Oficial. Consulta apenas conteúdo público, com intervalo entre
requisições. A responsabilidade pelo acompanhamento de publicações oficiais
continua sendo do usuário — use isto como auxílio, não como garantia.
