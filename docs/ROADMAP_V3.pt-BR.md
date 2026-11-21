# News Intelligence Engine — Roteiro público V3

**Situação:** proposta para discussão comunitária; **a V3 ainda não foi lançada**.  
**Idiomas:** [English](ROADMAP_V3.md) · Português (Brasil) (este documento)  
**Última revisão:** 21/11/2026

## Objetivo e escopo

Evoluir a ferramenta pública independente de pesquisa de notícias, mantendo execução local, transparência e testes reproduzíveis. A V2 já oferece coleta configurável de RSS/Atom/JSON simples, HTTPS controlado, cache condicional, deduplicação, revisões em SQLite, fila persistente, dashboard/API local e classificação temática opcional por IA acionada manualmente.

A V3 é **um roteiro proposto**, sem prazo de entrega ou promessa de funcionalidades prontas. O projeto não comprova previsões financeiras e não executa operações. Exemplos devem ser sintéticos ou ter autorização expressa para redistribuição.

## Prioridades e tarefas abertas

| Prioridade | Frente | Issue inicial | Objetivo | Como comprovar |
|---|---|---|---|---|
| P0 | Robustez dos feeds | [#6](https://github.com/MandrakBR007/news-intelligence-engine/issues/6) | Tratar entradas incompletas, malformadas e extensas em RSS/Atom/JSON | Testes sintéticos offline sem enfraquecer limites de segurança |
| P0 | Proveniência temporal e revisões | [#7](https://github.com/MandrakBR007/news-intelligence-engine/issues/7) | Diferenciar publicação informada pela fonte dos horários locais de observação | Casos reproduzíveis com datas ausentes, duplicatas e revisões |
| P0 | Avaliação da classificação temática | [#8](https://github.com/MandrakBR007/news-intelligence-engine/issues/8) | Benchmark sintético bilíngue para categorias de notícias | Matriz de confusão, métricas por categoria e limitações explícitas |
| P1 | Confiabilidade da integração opcional de IA | [#9](https://github.com/MandrakBR007/news-intelligence-engine/issues/9) | Testes com respostas simuladas, privacidade e tratamento de falhas | Testes sem chamadas externas no CI e sem vazamento de segredos |
| P1 | Diagnóstico e observabilidade | Proposta: discutir antes | Saúde local, estado de fontes e fila, erros resumidos | Saídas determinísticas que não divulguem credenciais |
| P2 | Experiência de uso e acessibilidade | Proposta: discutir antes | Guias bilíngues, acessibilidade e mensagens mais claras | Verificação manual e testes offline documentados |
| P2 | Experiência do desenvolvedor | Proposta: discutir antes | Esquemas locais de leitura e exemplos de integração | Plano de compatibilidade, testes sintéticos e versionamento |

**Prioridades:** P0 = integridade e segurança; P1 = confiabilidade; P2 = facilidade de uso e extensibilidade. Não representam prazos.

## Etapas propostas (sem datas prometidas)

**Etapa A — Especificações e exemplos.** Registrar hipóteses, comportamento atual e casos sintéticos antes de implementar mudanças.

**Etapa B — Implementação focada.** Pull Requests pequenos, testes de regressão e integrações externas sempre opcionais e explicitamente acionadas.

**Etapa C — Validação e documentação.** CI offline, revisão do CodeQL, análise pelos mantenedores e atualização de guias em ambos os idiomas. Receber feedback antes de declarar uma funcionalidade concluída.

## Critérios para concluir uma tarefa

1. Comportamento, riscos e interfaces afetadas documentados na Issue ou no Pull Request.
2. Testes sintéticos e reproduzíveis, sem internet, incluindo dados ausentes, inválidos e repetidos quando aplicável.
3. Aprovação de `python -B -m unittest discover -s tests -v` e `python -B tools/check_public_package.py`.
4. Checks obrigatórios do GitHub Actions aprovados e alertas pertinentes do CodeQL avaliados.
5. Ausência de credenciais reais, dados privados, lógica proprietária, endpoints privados ou material de terceiros sem licença adequada.
6. Documentação em inglês e português quando houver mudanças visíveis para o usuário.

## Limites deste projeto

- Sem chamadas automáticas não autorizadas a serviços de IA, segredos embutidos, execução em segundo plano por padrão ou dependência paga obrigatória.
- Sem execução de ordens, integração com contas financeiras ou afirmações de capacidade comprovada de prever mercados.
- Sem inventar horários de publicação nem apresentar dados históricos como observações prospectivas.
- Não enfraquecer os controles de HTTPS, DNS, tamanho de respostas, API restrita a loopback e saída segura no terminal.
- Vulnerabilidades devem ser comunicadas pela [política de segurança](../SECURITY.pt-BR.md), nunca com detalhes sensíveis em Issues públicas.

## Como participar

Escolha uma tarefa na página de [Issues](https://github.com/MandrakBR007/news-intelligence-engine/issues) ou apresente novas ideias em [Discussions](https://github.com/MandrakBR007/news-intelligence-engine/discussions). Faça alterações pequenas, associe o PR à Issue e siga o [guia de contribuição](../CONTRIBUTING.pt-BR.md). Este roteiro não impede novas propostas criativas.
