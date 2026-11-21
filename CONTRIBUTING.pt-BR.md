# Guia de contribuição

**Idiomas:** [English](CONTRIBUTING.md) · Português (Brasil) (este guia)

Obrigado por colaborar com o News Intelligence Engine. Esta edição é independente, utiliza dados públicos configurados pelo usuário e prioriza execução local.

## Antes de começar

- Utilize Python 3.11+ e execute `python -B -m unittest discover -s tests -v`.
- Não envie credenciais, tokens, dados pessoais, logs privados ou conteúdo de terceiros sem permissão.
- Exemplos e testes devem usar apenas dados sintéticos.
- Preserve o núcleo sem dependências obrigatórias; integrações externas devem ser opcionais e iniciadas explicitamente.

## Como contribuir

1. Para erros, abra uma Issue com descrição, passos para reproduzir e ambiente, sem dados sensíveis.
2. Para novas funcionalidades, descreva o problema e a proposta em uma Issue.
3. Crie uma branch específica para a alteração.
4. Inclua testes offline para comportamentos novos ou corrigidos.
5. Execute os testes e o verificador `python -B tools/check_public_package.py`.
6. Abra um Pull Request explicando o que mudou e como foi testado.

Ao enviar uma contribuição, você concorda que o conteúdo poderá ser distribuído conforme a [licença MIT](LICENSE). Envie somente material que você tenha direito de licenciar.

## Boas primeiras contribuições

- Melhorias de documentação e tradução.
- Casos sintéticos de feeds RSS, Atom e JSON malformados.
- Mensagens de erro mais claras.
- Melhor documentação da proveniência de horários e revisões de notícias.

Evite alterações de grande escopo sem uma discussão prévia. Não inclua chamadas de rede nos testes automatizados.

## Segurança

Não divulgue vulnerabilidades sensíveis em Issues públicas. Consulte [SECURITY.pt-BR.md](SECURITY.pt-BR.md) ou [SECURITY.md](SECURITY.md).

## Código de conduta

As contribuições seguem o [Código de Conduta](CODE_OF_CONDUCT.md). As mudanças são revisadas pelos mantenedores antes da integração.
