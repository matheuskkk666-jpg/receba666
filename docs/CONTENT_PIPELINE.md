# Pipeline de conteúdo offline

Fontes autorizadas ficam somente em `.local/content_sources/` e nunca são commitadas.

```powershell
python tools/content_pipeline.py normalize .local/content_sources/pt.txt .local/pt.json --language pt_BR --source-alias volume-01-pt --chapter-source-id arc01.ch01
python tools/content_pipeline.py normalize .local/content_sources/en.txt .local/en.json --language en --source-alias volume-01-en --chapter-source-id arc01.ch01
python tools/content_pipeline.py validate --pt_BR .local/pt.json --en .local/en.json --alignment pipeline/alignment.json
python tools/content_pipeline.py import --pt_BR .local/pt.json --en .local/en.json --alignment alignment.json --ledger pipeline/ledger.json --output game/generated --dry-run
```

O TXT UTF-8 é separado apenas por parágrafos vazios; o texto de cada bloco é preservado. O alignment versionado lista explicitamente os blocos de cada edição por unidade narrativa e permite vários blocos por idioma. O ledger versionável fixa `unit_id -> narrative_id` com fingerprints por edição. Se um unit conhecido mudar, a importação falha com conflito; ela nunca reutiliza um ID silenciosamente.

O mapa `alignment.json` tem `units`: cada unidade declara um `unit_id`, `chapter_id` e as listas de IDs-fonte `pt_BR` e `en`. Pode declarar um `narrative_id` explícito quando a equipe editorial já o definiu. Todo bloco normalizado deve aparecer uma vez no mapa; o comando `validate` falha se houver bloco duplicado, desconhecido ou não mapeado.

Arquivos gerados compatíveis com o loader ficam em fragments `narrative/` e `translations/<idioma>/`. O operador acrescenta esses fragments, a ordem canônica, cenas e metadados de capítulo ao manifest na revisão editorial; o importer não inventa direção visual. Scenes e direção seguem uma etapa editorial separada. Dry-run não escreve output nem ledger. O relatório apresenta cobertura por idioma (`source_blocks`, `mapped_blocks`, `unmapped_blocks`), IDs e conflitos.

O ledger e o alignment são versionáveis. As fontes em `.local/content_sources/` e saídas temporárias em `.local/` não são. Para uma alteração real: normalize as duas edições, revise o alignment, execute `import --dry-run`, resolva qualquer conflito explícito e só então execute o import normal. Um conflito de fingerprint nunca substitui texto nem IDs automaticamente.
