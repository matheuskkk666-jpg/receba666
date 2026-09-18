# Re:Zero Interactive Light Novel

Projeto privado de visual novel cinematográfica em Ren'Py, inicialmente focado em Windows 1080p (16:9).

## Princípios
- História linear: sem escolhas, combate ou QTE.
- Texto integral da fonte autorizada/fornecida.
- Português e inglês como edições independentes.
- Direção visual baseada em dramatic beats, não em quantidade de falas.
- Dois modos de apresentação: **Estático** e **Cinematográfico**.
- Prioridade: história > arte > atmosfera > animação > interface > mecânicas.

## Desenvolvimento
A implementação deve acontecer por branches e Pull Requests. A branch `main` representa apenas estados revisados.

Leia `AGENTS.md` e a documentação em `docs/` antes de alterar o projeto.

## Fundação executável

A fundação contém uma cena técnica curta e original. Ela
exercita o Scene Director data-driven, localização PT-BR/EN por ID estável,
modos Estático/Cinematográfico, menus, histórico e save/load. Não contém texto,
arte ou áudio de Re:Zero.

`game/content/manifest.json` versiona a composição do conteúdo e declara os
fragments de narrativa, cenas e traduções que devem ser carregados em ordem.

### Validação local

Com Python 3 disponível:

```powershell
python tools/validate.py
python -m unittest discover -s tests -v
```

Com o Ren'Py SDK 8.5.3, execute a partir da raiz do projeto:

```powershell
<python-do-sdk> <sdk>/renpy.py . lint
<python-do-sdk> <sdk>/renpy.py . test foundation --report-detailed
```

O preview de desenvolvimento aceita as variáveis `LN_PREVIEW_SCENE`,
`LN_PREVIEW_ID`, `LN_PREVIEW_LANGUAGE` (`pt_BR`/`en`) e `LN_PREVIEW_MODE`
(`static`/`cinematic`). Elas permitem abrir diretamente a cena/posição desejada
sem criar um fluxo separado de conteúdo.
