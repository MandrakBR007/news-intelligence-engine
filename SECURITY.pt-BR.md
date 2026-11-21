# Política de segurança

**Idiomas:** [English](SECURITY.md) · Português (Brasil) (esta página)

## Como comunicar uma vulnerabilidade

Não crie uma Issue pública contendo detalhes sensíveis. Utilize um canal privado disponibilizado pelos mantenedores, preferencialmente a função **Report a vulnerability** / aviso privado de segurança do GitHub, se estiver habilitada.

Inclua uma descrição curta, passos para reproduzir usando dados sintéticos, versão ou commit afetado e possíveis medidas de mitigação. Os mantenedores deverão avaliar o relato antes de qualquer divulgação pública.

## Escopo

- A aplicação é projetada para execução local.
- O repositório não deve conter credenciais, bancos operacionais, logs privados nem conteúdo confidencial.
- A coleta de feeds é iniciada explicitamente; a integração de IA é opcional.
- A interface web local é limitada a loopback e não foi projetada para exposição pública na internet.
- A classificação temática não constitui previsão financeira validada.

## Proteção de segredos

- Não publique chaves de API, tokens, senhas ou endpoints privados em Issues, Pull Requests, exemplos ou arquivos do repositório.
- O arquivo `.env` deve permanecer fora do Git. Use apenas `.env.example` com valores de exemplo vazios.
- Se uma credencial for exposta, revogue ou substitua a credencial imediatamente; reescrever o histórico não revoga uma credencial comprometida.

## Dependências

O núcleo utiliza somente a biblioteca padrão Python. Integrações opcionais exigem revisão de segurança, instalação voluntária e documentação adequada.
