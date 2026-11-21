# News Intelligence Engine — Versão Pública V2

**Idiomas:** [English](README.md) · Português (Brasil) (esta página)

Ferramenta independente para **pesquisa de notícias econômicas públicas**, com coleta configurável, deduplicação, histórico de revisões, horários de observação e dashboard local.

**Escopo:** biblioteca demonstrativa de processamento de dados. Os classificadores por palavras-chave e as avaliações opcionais de IA não comprovam capacidade de prever mercados.

## Funcionalidades

- Feeds RSS 2.0, Atom 1.0 e JSON simples configurável.
- HTTPS com limite de 2 MB por resposta, rejeição de redirecionamentos e endereços privados, validação de DNS e conexão ao IP verificado.
- Cache condicional `ETag` / `Last-Modified` e suporte a resposta `304`.
- Agrupamento por similaridade, identificação de duplicatas e histórico das revisões.
- Horários UTC separados: publicação (quando conhecida), primeiro recebimento, ingestão e classificação.
- Fila SQLite persistente com lease, retentativas e processamento manual por tarefa.
- Dashboard e API HTTP exclusivamente em loopback.
- Exemplo opcional de **Gemini Decision 1**, limitado à classificação genérica de temas e invocado manualmente.

## Começando sem internet

Recomendado Python 3.11+.

```bash
python -B -m unittest discover -s tests -v
python -B -m news_engine demo --data-dir data
python -B -m news_engine stats --data-dir data
```

A demonstração usa somente dados sintéticos. Nada é enviado a serviços externos.

## Coleta real de feeds públicos (ação explícita)

Copie `examples/config.example.json` para `config.json` e substitua a URL de exemplo por uma fonte HTTPS pública e autorizada. Depois execute:

```bash
python -B -m news_engine collect --config config.json --data-dir data
python -B -m news_engine serve --config config.json --data-dir data
```

A interface fica em `http://127.0.0.1:8080/`.

Para testar a fila persistente:

```bash
python -B -m news_engine enqueue-feeds --config config.json --batch-id rodada-1 --data-dir data
python -B -m news_engine work-once --config config.json --data-dir data
python -B -m news_engine queue-stats --data-dir data
```

Cada chamada `work-once` executa no máximo uma tarefa. **Não há agendamento automático** nesta edição.

## Gemini Decision 1 opcional

Instale `requirements-optional.txt`, defina `GEMINI_API_KEY` na variável de ambiente e altere `gemini.enabled` para `true` em `config.json`. Execute explicitamente:

```bash
python -B -m news_engine review --config config.json --item-id 1 --data-dir data
```

Essa chamada envia título e resumo à API Google. O exemplo usa perguntas públicas de classificação temática, sem previsão financeira. Sua chamada externa não foi executada nos testes offline deste pacote.

## Como participar

É possível contribuir relatando erros, propondo funcionalidades e enviando Pull Requests. Utilize dados sintéticos nos exemplos e nos testes. Comece pelo [guia de contribuição em português](CONTRIBUTING.pt-BR.md), ou pelo [guia em inglês](CONTRIBUTING.md).

**Segurança:** nunca publique chaves de API, tokens ou dados sensíveis em Issues. Para vulnerabilidades, veja [Política de segurança em português](SECURITY.pt-BR.md) ou [Security Policy](SECURITY.md).

## Contribuições e licença

Os modelos de Issues e Pull Requests estão incluídos. O projeto usa a [licença MIT](LICENSE) e segue o [Código de Conduta](CODE_OF_CONDUCT.md). Contribuições passam pela revisão dos mantenedores. Esta versão não oferece previsões financeiras validadas nem execução de operações.
