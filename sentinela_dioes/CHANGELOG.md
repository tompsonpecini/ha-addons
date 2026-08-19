# Changelog

## 2.1.0

- Notificação enxuta: mostra o termo encontrado e onde saiu, agrupado por termo,
  em vez de despejar o texto da matéria.
- Novas opções `incluir_trecho` e `incluir_link`, ambas desligadas por padrão.
- Regex vira rótulo legível na notificação (`\bPECINI\b` aparece como `PECINI`).

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
