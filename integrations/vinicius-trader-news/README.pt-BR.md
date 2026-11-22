# Vinicius Trader — Integração isolada de notícias (sanitizada)

**Status:** pacote de referência independente e sanitizado para coleta de notícias; não instalado nem integrado automaticamente.

Documentação técnica: [Português (Brasil)](docs/INTEGRACAO_TECNICA_PTBR.txt) · [English](docs/INTEGRATION_TECHNICAL_EN.txt).

**Crédito pela contribuição:** Vinicius Trader (pacote recebido e melhorias propostas, conforme informado pelo destinatário). Mantida a licença MIT original em [LICENSE](LICENSE).

Foram removidos a integração de IA externa, instruções de credenciais, banco de notícias do remetente e artefatos gerados. Os endpoints `/api` remanescentes pertencem a uma interface HTTP local somente leitura.

**Demonstração offline:** `python -B -m news_engine demo --data-dir ./local_demo`.

**Não descompactar sobre o projeto principal nem integrar automaticamente à produção.** É um artefato independente de avaliação.
