# News Intelligence Engine — Versão Pública V2

**Idiomas:** [English](README.md) · Português (Brasil) (esta página)

Ferramenta independente para **pesquisa de notícias econômicas públicas**, com coleta configurável, deduplicação, histórico de revisões, horários de observação e dashboard local.

**Escopo:** biblioteca demonstrativa de processamento de dados. Os classificadores por palavras-chave e as avaliações opcionais de IA não comprovam capacidade de prever mercados.

## Roteiro público V3 (proposta)

As próximas prioridades estão no [Roteiro V3 em português](docs/ROADMAP_V3.pt-BR.md) e no [V3 Roadmap em inglês](docs/ROADMAP_V3.md). São **propostas, não funcionalidades já entregues**. As primeiras tarefas estão nas [Issues #6–#9](https://github.com/MandrakBR007/news-intelligence-engine/issues?q=is%3Aissue+is%3Aopen+%22%5BV3%5D%22). Novas ideias podem ser discutidas em [Discussions](https://github.com/MandrakBR007/news-intelligence-engine/discussions).

## Funcionalidades

- Feeds RSS 2.0, Atom 1.0 e JSON simples configurável.
- HTTPS com limite de 2 MB por resposta, rejeição de redirecionamentos e endereços privados, validação de DNS e conexão ao IP verificado.
- Cache condicional `ETag` / `Last-Modified` e suporte a resposta `304`.
- Agrupamento por similaridade, identificação de duplicatas e histórico das revisões.
- Horários UTC separados: publicação (quando conhecida), primeiro recebimento, ingestão e classificação.
- Fila SQLite persistente com lease, retentativas e processamento manual por tarefa.
- Dashboard e API HTTP exclusivamente em loopback.
- Exemplo opcional de **Gemini Decision 1**, limitado à classificação genérica de temas e invocado manualmente.

## Instalação local opcional (compatível com V2)

No Python 3.11+, é possível instalar o núcleo sem dependências obrigatórias externas:

```bash
python -m pip install -e .
news-engine demo --data-dir data
```

O comando anterior `python -B -m news_engine` continua funcionando. Para a integração opcional e **manual** com IA, use `pip install -e ".[gemini]"`; para ferramentas de desenvolvimento, `pip install -e ".[dev]"`. Consulte as [notas de engenharia](docs/ENGINEERING_V3.md). A instalação não inicia coleta externa nem serviço automático.

## Benchmark experimental de deduplicação (proposta V3)

Um [benchmark sintético e offline](docs/DEDUP_BENCHMARK.md) verifica pares semelhantes e falsos agrupamentos. Execute `python -m tools.benchmark_dedup` na raiz do projeto. A opção `dedup.compare_stored_tokens` permite comparar Jaccard com textos persistidos, mas está **desativada por padrão** e não altera IDs históricos. As métricas sintéticas não representam acurácia real.

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
