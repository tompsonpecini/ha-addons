# Changelog

## 2.2.1

- **Corrigido: o rótulo do termo na notificação.** A função que transforma o
  regex em texto legível apagava o `|` sem deixar rastro, então
  `\bSILVA\b|\bSOUZA\b` aparecia como "SILVASOUZA" — indistinguível de um
  sobrenome composto, o que já levou a uma leitura errada de um log. Agora a
  alternação vira " / ".
- Curingas, classes e atalhos (`.{0,12}`, `[-\s]?`, `\s*`) viram o espaço que
  de fato separa as partes do nome: `\bCRM\b.{0,12}\b1234\b` aparece como
  "CRM 1234" e `\bMARIA\b.{0,25}SOUZA\b` como "MARIA SOUZA". Antes o alerta e
  o relatório mostravam o padrão cru.

## 2.2.0

- **Corrigido: a notificação não abria nada.** O caminho que funcionava era o
  de reserva (`notify.send_message`), que ignora `data` — sem `url`, tocar no
  alerta só abre o dashboard padrão do app. O add-on agora avisa no log quando
  cai para a reserva e, quando o `notify_service` não existe, lista os serviços
  `notify` disponíveis em vez de deixar só o HTTP 400 seco.
- **Novo: página de relatório.** Cada varredura com achados grava
  `<config>/www/sentinela_dioes/ultimo.html` e a notificação aponta para ela.
  Traz as ocorrências agrupadas por edição, com trecho, termo destacado e link
  para o portal. Exige `homeassistant_config:rw`, acrescentado ao mapeamento.
- Uma ocorrência por página e por termo. O mesmo termo repetido cinco vezes na
  mesma página virava cinco linhas iguais na notificação; agora vira uma, com a
  contagem de repetições no relatório.
- `incluir_link` passa a valer `true` por padrão e agora anexa o relatório.

## 2.1.0

- Notificação enxuta: mostra o termo encontrado e onde saiu, agrupado por termo,
  em vez de despejar o texto da matéria.
- Novas opções `incluir_trecho` e `incluir_link`, ambas desligadas por padrão.
- Regex vira rótulo legível na notificação (`\bSILVA\b` aparece como `SILVA`).

## 2.0.2

- Corrigido: acrescentar um termo novo não fazia efeito nas edições já
  processadas, então o termo só valeria para publicações futuras. O add-on
  agora guarda uma assinatura da lista e reprocessa a janela quando ela muda.

## 2.0.1

- Corrigido: no modo de download completo, o PDF de prova não era gravado em
  `achados/`. A pasta ficaria vazia mesmo havendo ocorrência.
- Fim de semana e feriado deixam de ser registrados como AVISO. "Edição não
  existente" em dia sem publicação é resposta correta do portal.

## 2.0.0

- Passa a consultar a API do portal **por data**, em vez de adivinhar números de
  edição incrementando IDs. Elimina as opções `edicao_inicial`, `janela_base`,
  `janela_max`, `max_paginas` e `filtro_diario`.
- Edições extras e suplementos da mesma data passam a ser varridos.
- Baixa a edição inteira num único arquivo quando o portal permite, reduzindo
  de centenas de requisições para meia dúzia por ciclo.
- Verificação de sanidade compara as páginas lidas com as anunciadas pela API.

Motivo da mudança: os IDs são globais no sistema IOES, que hospeda também
diários municipais. Incrementar o ID levava a varrer o jornal errado.

## 1.0.0

- Primeira versão.
