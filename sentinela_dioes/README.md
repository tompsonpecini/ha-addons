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
| `incluir_link` | false | Torna a notificação clicável, abrindo o Diário |
| `notify_service` | — | Serviço clássico, ex.: `mobile_app_meu_iphone` |
| `notify_entity` | — | Entidade notify, ex.: `notify.meu_celular` |
| `horarios` | 07/13/19 | Horários das varreduras |
| `pausa_segundos` | 0.4 | Intervalo entre requisições ao portal |

Se ambos os campos de notificação estiverem preenchidos, o serviço clássico é
tentado primeiro (aceita link e som), com o moderno como reserva.

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
