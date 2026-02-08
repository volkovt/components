# Componentes — UI Kit + Theme Engine + Tables + Export (PySide6/QtPy)

Uma **base reutilizável de componentes** para aplicações desktop de gestão em Python, construída sobre **PySide6** (via **QtPy**) e pensada como fundação para um produto maior (offline-first, multiplataforma, evolutivo).

Este repositório entrega:

- **Theme Engine** baseado em *design tokens* (JSON) + QSS
- **UI Kit (App\*)** com padrões de UX consistentes (states, variantes, containers, dialogs, feedback)
- **Tabelas “next-gen”** com busca/filtros/ordenação/paginação/seleção
- **Exportação profissional** (XLSX e PDF) com **Use Case + Ports + Infra**, sem acoplar UI ao formato de saída

## Sumário

- [Executar a demo](#executar-a-demo)
- [Arquitetura e princípios](#arquitetura-e-princípios)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Theme Engine](#theme-engine)
- [UI Kit (App\*)](#ui-kit-app)
- [Tabelas (AppTable)](#tabelas-apptable)
- [Exportação (XLSX/PDF)](#exportação-xlsxpdf)
- [Ports & DTOs (contratos)](#ports--dtos-contratos)
- [Exemplos de uso](#exemplos-de-uso)
- [Assets](#assets)
- [Dependências](#dependências)
- [Empacotamento (Nuitka)](#empacotamento-nuitka)
- [Roadmap](#roadmap)

---

## Executar a demo

A aplicação `main.py` (ou o `main_updated.py`) é a vitrine oficial do que foi construído.

### 1) Instalar dependências

```bash
pip install -r requirements.txt
```

### 2) Rodar

```bash
python main.py
# ou
python main_updated.py
```

Você verá uma janela com abas demonstrando:

- Gallery (visão rápida)
- Typography, Buttons, Inputs, Containers, Views
- Feedback & Dialogs
- Next-Gen Tables
- Theme & Assets
- Icons
- Export (PDF/XLSX)
- Ports & DTOs
- CRUD Mock (exemplo in-memory com filtro + ações + dialogs)

---

## Arquitetura e princípios

Este projeto é construído para **escala técnica** (crescer sem virar “monolito de UI”) e adota separações claras:

### Fluxo principal (Clean-ish / Ports & Adapters)

**UI → Use Cases → Ports (Interfaces) → Infra (implementações)**

- **UI**: widgets, telas, tabelas, dialogs — *sem regra de negócio pesada* e sem dependência direta de “infra”.
- **Use Cases**: orquestram fluxo (ex.: exportação), validam e chamam ports.
- **Ports**: contratos (Protocol / dataclasses) para dados tabulares e exporters.
- **Infra**: implementações concretas (XLSX/PDF), prontas para serem trocadas.

### Convenções fortes de UI (QSS + dynamic properties)

Todos os widgets do kit seguem um padrão de estilo via **dynamic properties**:

- `role`: `"title" | "subtitle" | "muted" | "badge" | "card" | ...`
- `state`: `"success" | "warning" | "error" | ""`
- `variant`: `"primary" | "ghost" | "danger" | "default" | "tool"`
- `busy`: `bool` (ex.: carregando)
- `disabled`: `bool`

A função `repolish(widget)` é o mecanismo para “forçar” o Qt a reaplicar QSS após mudar propriedades.

### Performance: UI thread não pode travar

Operações pesadas (ex.: exportar milhares de linhas) devem rodar fora da UI thread.
A demo já inclui padrão com `QThreadPool + QRunnable` e sinais (progress/finished/error).

---

## Estrutura do projeto

Estrutura lógica:

```
app/
  core/
    dto/
      export_dto.py
    ports/
      exporter_registry.py
      table_exporter_port.py
      table_ports.py
    ui/
      __init__.py
      app_theme.py
      application.py
      base.py
      buttons.py
      containers.py
      dialogs.py
      feedback.py
      icon_theme.py
      inputs.py
      layout.py
      messagebox.py
      scroll.py
      tables.py
      tabs.py
      theme_manager.py
      theme_types.py
      typography.py
      views.py
      window.py
    use_cases/
      export_table.py
  infra/
    export/
      excel/xlsx_exporter.py
      pdf/pdf_exporter.py

assets/
  icons/
    excel.svg
    pdf.svg
  qss/
    base.qss
    buttons.qss
    dialogs.qss
    inputs.qss
    main.qss
    tabs.qss
    typography.qss
    views.qss
  themes/
    light.json
    dark.json
    density_compact.json
    density_regular.json
    density_comfortable.json
```

---

## Theme Engine

O Theme Engine é composto por **tokens JSON + QSS** e centraliza toda a identidade visual.

### Tokens (JSON)

- `assets/themes/light.json`
- `assets/themes/dark.json`

Eles definem cores, bordas, sombras, tamanhos-base etc.

### Density (espaçamento e sizing)

- `assets/themes/density_compact.json`
- `assets/themes/density_regular.json`
- `assets/themes/density_comfortable.json`

Permite um app “compacto” (mais linhas em tela) ou “confortável” (mais respiro).

### QSS

- `assets/qss/main.qss` referencia/importa os parciais:
  - `base.qss`, `buttons.qss`, `inputs.qss`, `dialogs.qss`, `tabs.qss`, `typography.qss`, `views.qss`

### Como funciona

- `ThemeManager`:
  - carrega tokens + density
  - compila QSS (template)
  - faz cache por fingerprint (útil para hot reload)
- `AppTheme`:
  - é o “facade” que une `ThemeManager` + `IconTheme`
  - método `apply(app)` aplica o QSS no `QApplication`

### Variáveis de ambiente úteis

- `APP_PROJECT_ROOT`: sobrescreve o root (quando rodando empacotado ou em monorepo)
- `APP_THEME_HOT_RELOAD=1`: liga hot reload do tema (modo dev)

---

## UI Kit (App\*)

O objetivo do kit é **padronizar UI/UX** com componentes consistentes e simples de compor.

### Superfície pública estável

Import preferencial (API “oficial”):

```py
from app.core.ui import PrimaryButton, AppLineEdit, Card, AppDialog, InlineStatus, AppTable
```

O `app/core/ui/__init__.py` expõe o conjunto principal (evita “importes profundos” em toda a base).

### Catálogo de componentes

#### Tipografia
- `TitleLabel`, `SubtitleLabel`, `MutedLabel`, `Badge`

#### Botões
- `AppButton` (base)
- `PrimaryButton`, `GhostButton`, `DangerButton`
- `AppToolButton` (toolbar e ações compactas)

#### Inputs (com validação + estado visual)
- `AppLineEdit` (required + validator + validate_fn)
- `AppMoneyLineEdit` (valor monetário com locale)
- `AppTextEdit`, `AppPlainTextEdit`
- `AppComboBox` (required opcional)
- `AppSpinBox`, `AppDoubleSpinBox`
- `AppDateEdit`, `AppTimeEdit`, `AppDateTimeEdit`
- helpers: `int_validator(...)`, `money_validator(...)`

#### Containers / Layout
- `Card`, `Section`, `Divider`, `Toolbar`
- helpers: `vbox(...)`, `hbox(...)`
- `AppScrollArea`

#### Feedback
- `InlineStatus` (info/success/warning/error)
- `AppProgressBar`

#### Dialogs
- `AppDialog`, `FormDialog`
- `DialogSizePreset`
- `confirm_destructive(...)`

#### Views
- `AppTableView` + `SimpleTableModel` (tabela simples e direta)
- `AppTabWidget`
- `AppMessageBox`
- `AppMainWindow`, `AppApplication`

---

## Tabelas (AppTable)

`AppTable` é o componente de tabela “avançado” para apps de gestão.

### O que ele entrega

- Busca textual (incluindo modos mais avançados dependendo da configuração)
- Filtros (`FilterSpec`)
- Ordenação (`SortSpec`)
- Paginação (offset/limit) e experiência “fluida”
- Seleção de linhas (para ações e export “selected_rows”)
- Integração com **export** (Use Case + Infra)

### Dados via Port (sem acoplar a UI ao armazenamento)

A tabela não precisa saber se vem de memória, banco, API etc.  
Você fornece um `TableDataPort`.

- `InMemoryTablePort` já existe para demos e protótipos.
- A mesma porta permite evoluir para SQLAlchemy/SQLite/MySQL depois.

---

## Exportação (XLSX/PDF)

Exportação foi construída como **fluxo completo com separação de camadas**.

### Use Case

- `app/core/use_cases/export_table.py` → `ExportTableUseCase`
- Suporta `ExportMode`:
  - `all_results` (pagina e exporta tudo)
  - `current_page` (exporta a página atual)
  - `selected_rows` (exporta seleção)

### Ports

- `TableExporterPort`: interface única para qualquer formato
- `ExporterRegistry`: registro de exporters por `fmt`
- `TableDataPort`: porta para obter `rows(...)`, `columns(...)`, `total_count(...)`

### Infra (implementações concretas)

- XLSX: `app/infra/export/excel/xlsx_exporter.py` (openpyxl)
- PDF: `app/infra/export/pdf/pdf_exporter.py` (reportlab)

---

## Ports & DTOs (contratos)

Os contratos são intencionalmente simples e estáveis.

### DTO

- `ExportRequest` (fmt, destination_path, mode, report_title, query, columns, chunk_page_size)

### Portas

- `TableDataPort`: origem de dados tabulares
- `TableExporterPort`: exportação de tabela (PDF/XLSX/…)
- `ExporterRegistry`: resolve exporter pelo formato

Isso permite:

- trocar a fonte de dados sem reescrever UI
- adicionar novos formatos sem mexer no Use Case

---

## Exemplos de uso

### 1) Aplicar tema e densidade

```py
from app.core.ui import AppApplication, apply_app_theme, set_theme_mode, set_density, ThemeMode, Density

app = AppApplication([])
set_theme_mode(ThemeMode.DARK)
set_density(Density.REGULAR)
apply_app_theme(app)
```

### 2) Input com validação e estado visual

```py
from app.core.ui import AppLineEdit, int_validator

le = AppLineEdit(
    placeholder="Inteiro 0..9999",
    required=True,
    validator=int_validator(0, 9999),
)

result = le.validate_now()
if not result.ok:
    print(result.message)
```

### 3) Status inline (feedback rápido)

```py
from app.core.ui import InlineStatus, AppButton

status = InlineStatus()
btn = AppButton("Salvar", on_click=lambda: status.show_success("Operação OK."))
```

### 4) AppTable com fonte in-memory

```py
from app.core.ui import AppTable, InMemoryTablePort

rows = [
    {"id": 1, "name": "Produto A", "price": 10.5},
    {"id": 2, "name": "Produto B", "price": 25.0},
]

port = InMemoryTablePort(rows)
table = AppTable(port=port)
table.refresh()
```

### 5) Export headless (sem depender do widget)

```py
from app.core.use_cases.export_table import ExportTableUseCase, ExportRequest
from app.core.ports.exporter_registry import ExporterRegistry
from app.infra.export.excel.xlsx_exporter import XlsxTableExporter
from app.infra.export.pdf.pdf_exporter import PdfTableExporter

registry = ExporterRegistry(_exporters={
    "xlsx": XlsxTableExporter(),
    "pdf": PdfTableExporter(),
})

use_case = ExportTableUseCase(exporters=registry, data_port=port)  # port = TableDataPort
req = ExportRequest(fmt="xlsx", destination_path="relatorio.xlsx", mode="all_results")

result = use_case.execute(req, on_progress=lambda done, total: print(done, total))
print(result.path, result.rows_exported)
```

### 6) Adicionar um novo formato (ex.: CSV)

- implemente `TableExporterPort`
- registre no `ExporterRegistry` como `"csv": CsvExporter()`

---

## Assets

### Ícones
- `assets/icons/excel.svg`
- `assets/icons/pdf.svg`

### QSS
- `assets/qss/main.qss`
- parciais: `base.qss`, `buttons.qss`, `inputs.qss`, `dialogs.qss`, `tabs.qss`, `typography.qss`, `views.qss`

### Tokens
- `assets/themes/light.json`, `assets/themes/dark.json`
- `assets/themes/density_*.json`

---

## Dependências

Arquivo `requirements.txt`:

- `qtpy`
- `PySide6`
- `openpyxl`
- `reportlab`
- `qtawesome`

---

## Empacotamento (Nuitka)

A base é compatível com empacotamento, e o `base.py` já trata “frozen build” (resolve paths quando executável).

Exemplo de comando (ajuste conforme seu ambiente e necessidades):

```bash
python -m nuitka main.py \
  --standalone \
  --enable-plugin=pyside6 \
  --include-data-dir=assets=assets \
  --output-dir=build
```

**Dicas importantes:**
- garanta que `assets/` vá junto (QSS, themes, icons)
- use `APP_PROJECT_ROOT` em cenários específicos se o root precisar ser forçado
- teste no Windows e Linux, principalmente por causa de plugins do Qt

---

## Roadmap

Esta base foi construída como “núcleo” reutilizável. Próximos passos naturais:

1. **Adicionar Ports de persistência** (ex.: SQLAlchemy) respeitando `TableDataPort`
2. **Plug-in de módulos** (Estoque, Clientes, Tarefas) sobre esse kit
3. **Migrations** e troca de banco (SQLite ↔ MySQL) mantendo domínio e use cases independentes
4. **Mais exporters** (CSV, JSON, Impressão direta)
5. **Biblioteca/packaging** (publicar como pacote pip interno, versionamento semântico, changelog)

---

## Como usar esta base em outro projeto

Opções comuns:

1. **Vendor**: copie `app/core/ui`, `app/core/ports`, `app/core/use_cases`, `app/infra/export` e `assets/`
2. **Submodule** (git): inclua como submódulo e aponte o `PYTHONPATH`
3. **Package interno**: transforme em pacote e publique em um registry privado

O ponto crítico é manter:

- `assets/` ao lado do executável (ou acessível via `APP_PROJECT_ROOT`)
- imports sempre via `from app.core.ui import ...` para estabilidade

