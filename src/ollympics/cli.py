"""Typer CLI: `oly`.

Subcommands:
  oly models list          — installed Ollama models
  oly suites               — available suites
  oly db init              — create SQLite schema
  oly run --models ... --suites ...
  oly results show [--run-id N]
  oly serve --port 8000    — FastAPI dev server
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import select

from ollympics.core.config import settings
from ollympics.core.ollama import OllamaClient
from ollympics.core.runner import execute_run
from ollympics.db.models import Attempt, Model, Run, TaskRow
from ollympics.db.session import init_db, session_scope
from ollympics.schemas.run import RunConfig
from ollympics.schemas.runtime import RuntimeConfig
from ollympics.suites.loader import list_suites

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Ollympics CLI")
console = Console()

models_app = typer.Typer(no_args_is_help=True, help="Ollama models")
db_app = typer.Typer(no_args_is_help=True, help="Database")
results_app = typer.Typer(no_args_is_help=True, help="Results")
corpus_app = typer.Typer(no_args_is_help=True, help="RAG corpus management")
app.add_typer(models_app, name="models")
app.add_typer(db_app, name="db")
app.add_typer(results_app, name="results")
app.add_typer(corpus_app, name="corpus")


@corpus_app.command("generate")
def corpus_generate(
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Re-generate docs already on disk"
    ),
) -> None:
    """Genera el corpus sintético + qa.yaml usando el agente LangGraph + DeepSeek."""
    from ollympics.generators.synthetic_corpus.runner import generate_corpus

    console.print(
        Panel.fit(
            "[bold]Generador de corpus sintético[/bold]\n"
            "modelo: configurable via LLM_MODEL en .env\n"
            "proveedor: cualquiera compatible con OpenAI API",
            border_style="cyan",
        )
    )
    with console.status("[cyan]generando 4 docs + qa.yaml…[/cyan]", spinner="dots"):
        result = generate_corpus(overwrite=overwrite)

    if not result.docs_written:
        console.print(
            "[yellow]Sin docs nuevos. Usa --overwrite para regenerar.[/yellow]"
        )
    else:
        console.print(f"[green]✓[/green] Documentos generados:")
        for path in result.docs_written:
            console.print(f"  · [cyan]{path}[/cyan]")
        console.print(f"[green]✓[/green] Q&A YAML: [cyan]{result.qa_yaml_path}[/cyan]")
    console.print(f"[dim]prompts en: {result.prompts_dir}[/dim]")


@corpus_app.command("build")
def corpus_build(
    force: bool = typer.Option(False, "--force", help="Re-embed all chunks"),
) -> None:
    """Chunkea los 4 docs + embede con nomic-embed-text + persiste vectors.jsonl."""
    from ollympics.suites.rag.corpus import build_vector_store, vector_store_path

    with console.status("[cyan]chunking + embedding…[/cyan]", spinner="dots"):
        store = asyncio.run(build_vector_store(force=force))
    console.print(
        f"[green]✓[/green] Vector store: [cyan]{len(store)}[/cyan] chunks "
        f"en [cyan]{vector_store_path()}[/cyan]"
    )


@corpus_app.command("info")
def corpus_info() -> None:
    """Muestra qué chunks están indexados en el vector store."""
    from ollympics.core.vector_store import VectorStore
    from ollympics.suites.rag.corpus import vector_store_path

    store = VectorStore(vector_store_path())
    if len(store) == 0:
        console.print("[yellow]Vector store vacío. Corre `oly corpus build`.[/yellow]")
        return
    table = Table(title=f"Vector store · {len(store)} chunks")
    table.add_column("ID", style="cyan")
    table.add_column("Doc", style="magenta")
    table.add_column("Sección", style="dim")
    table.add_column("Chars", justify="right")
    for c in store.chunks:
        table.add_row(c.id, c.doc, c.section, str(len(c.text)))
    console.print(table)


@corpus_app.command("prompts")
def corpus_prompts() -> None:
    """Lista los prompts del generador (escribibles por el usuario)."""
    from ollympics.generators.synthetic_corpus.prompts import (
        PROMPT_FILES,
        write_default_prompts,
    )
    from ollympics.generators.synthetic_corpus.runner import prompts_dir

    pdir = prompts_dir()
    write_default_prompts(pdir)
    table = Table(title=f"Prompts en {pdir}")
    table.add_column("Archivo", style="cyan")
    table.add_column("Bytes", justify="right")
    for name in PROMPT_FILES:
        f = pdir / name
        table.add_row(name, str(f.stat().st_size) if f.exists() else "-")
    console.print(table)


# ---------- models ----------

@models_app.command("list")
def models_list() -> None:
    """List models installed in Ollama."""
    client = OllamaClient()
    models = asyncio.run(client.list_models())
    if not models:
        console.print("[yellow]No hay modelos instalados en Ollama.[/yellow]")
        return
    table = Table(title=f"Modelos en {settings.ollama_host}", show_lines=False)
    table.add_column("Nombre", style="cyan")
    table.add_column("Tamaño", justify="right")
    table.add_column("Modificado", style="dim")
    for m in models:
        size_mb = m.get("size", 0) // (1024 * 1024)
        table.add_row(m.get("name", "?"), f"{size_mb} MB", str(m.get("modified_at", ""))[:19])
    console.print(table)


# ---------- suites ----------

@app.command("suites")
def suites_cmd() -> None:
    """List available suites discovered in tasks/."""
    suites = list_suites()
    if not suites:
        console.print(f"[yellow]No hay suites en {settings.tasks_dir}[/yellow]")
        return
    from ollympics.suites.loader import load_suite

    table = Table(title="Suites disponibles")
    table.add_column("Suite", style="cyan")
    table.add_column("Tasks", justify="right")
    for s in suites:
        try:
            n = len(load_suite(s))
            table.add_row(s, str(n))
        except Exception as e:
            table.add_row(s, f"[red]error: {e}[/red]")
    console.print(table)


# ---------- db ----------

@db_app.command("init")
def db_init() -> None:
    """Create SQLite schema."""
    init_db()
    console.print(f"[green]✓[/green] DB inicializada en [cyan]{settings.db_path}[/cyan]")


# ---------- run ----------

@app.command("run")
def run_cmd(
    models: str = typer.Option(..., "--models", help="Comma-separated model names"),
    suites: str = typer.Option("baseline", "--suites", help="Comma-separated suite names"),
    num_ctx: int = typer.Option(8192, "--num-ctx"),
    kv_cache: str = typer.Option("f16", "--kv-cache"),
    notes: str | None = typer.Option(None, "--notes"),
) -> None:
    """Dispara una corrida de benchmark."""
    init_db()

    config = RunConfig(
        models=[m.strip() for m in models.split(",") if m.strip()],
        runtime_configs=[RuntimeConfig(num_ctx=num_ctx, kv_cache_type=kv_cache)],
        suites=[s.strip() for s in suites.split(",") if s.strip()],
        notes=notes,
    )

    console.print(
        Panel.fit(
            f"[bold]Modelos:[/bold] {', '.join(config.models)}\n"
            f"[bold]Suites:[/bold] {', '.join(config.suites)}\n"
            f"[bold]Runtime:[/bold] num_ctx={num_ctx}, kv_cache={kv_cache}",
            title="Run config",
            border_style="cyan",
        )
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("Evento", style="dim", width=18)
    table.add_column("Detalle")

    async def on_event(event: str, payload: dict) -> None:
        style = {
            "run.started": "cyan",
            "model.started": "magenta",
            "model.finished": "magenta",
            "suite.started": "blue",
            "suite.finished": "blue",
            "task.finished": "green" if payload.get("status") == "success" else "yellow",
            "task.skipped": "dim",
        }.get(event, "white")

        detail_parts = []
        for k, v in payload.items():
            if k in ("ttft_ms", "tps_decode") and v is not None:
                if k == "tps_decode":
                    detail_parts.append(f"{k}={v:.1f}")
                else:
                    detail_parts.append(f"{k}={v}")
            elif k != "run_id":
                detail_parts.append(f"{k}={v}")
        detail = " ".join(detail_parts)
        console.print(f"  [{style}]{event:<18}[/{style}] {detail}")

    try:
        run_id = asyncio.run(execute_run(config, on_event=on_event))
        console.print(f"\n[green bold]✓ Run #{run_id} terminado[/green bold]")
        console.print(f"  ver detalle: [cyan]oly results show --run-id {run_id}[/cyan]")
    except KeyboardInterrupt:
        console.print("\n[red]Interrumpido por usuario[/red]")
        raise typer.Exit(130) from None


# ---------- sweep (Fase 10) ----------

@app.command("sweep")
def sweep_cmd(
    models: str = typer.Option(..., "--models", help="Comma-separated model names"),
    suites: str = typer.Option("baseline", "--suites", help="Comma-separated suite names"),
    num_ctx: str = typer.Option(
        "8192", "--num-ctx", help="Comma-separated num_ctx values, e.g. '2048,4096,8192'"
    ),
    kv_cache: str = typer.Option(
        "f16", "--kv-cache", help="Comma-separated KV cache types, e.g. 'f16,q8_0,q4_0'"
    ),
    notes: str | None = typer.Option(None, "--notes"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Solo imprime el plan, no ejecuta"),
) -> None:
    """Producto cartesiano de (modelo × num_ctx × kv_cache) sobre las suites.

    Cada combinación se ejecuta como un Run independiente, lo que permite
    compararlos directamente en el Leaderboard (cada uno tiene su propio
    runtime_hash).
    """
    init_db()

    model_list = [m.strip() for m in models.split(",") if m.strip()]
    suite_list = [s.strip() for s in suites.split(",") if s.strip()]
    num_ctx_list = [int(x.strip()) for x in num_ctx.split(",") if x.strip()]
    kv_list = [x.strip() for x in kv_cache.split(",") if x.strip()]

    combos: list[tuple[str, int, str]] = [
        (m, n, k) for m in model_list for n in num_ctx_list for k in kv_list
    ]

    table = Table(title="Sweep plan", show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Modelo", style="cyan")
    table.add_column("num_ctx", justify="right")
    table.add_column("kv_cache")
    for i, (m, n, k) in enumerate(combos, 1):
        table.add_row(str(i), m, str(n), k)
    console.print(table)
    console.print(f"[bold]Total combos:[/bold] {len(combos)} · suites: {', '.join(suite_list)}")

    if dry_run:
        console.print("[yellow]--dry-run, no ejecuto[/yellow]")
        return

    completed: list[tuple[int, str, int, str]] = []
    for idx, (m, n, k) in enumerate(combos, 1):
        console.print(
            f"\n[bold cyan]→ {idx}/{len(combos)}[/bold cyan]  {m}  num_ctx={n}  kv={k}"
        )
        config = RunConfig(
            models=[m],
            runtime_configs=[RuntimeConfig(num_ctx=n, kv_cache_type=k)],
            suites=suite_list,
            notes=(notes or "sweep") + f" · {m} ctx={n} kv={k}",
        )
        try:
            run_id = asyncio.run(execute_run(config))
            console.print(f"  [green]✓[/green] Run #{run_id}")
            completed.append((run_id, m, n, k))
        except KeyboardInterrupt:
            console.print("\n[red]Sweep interrumpido[/red]")
            break

    summary = Table(title=f"Sweep terminado · {len(completed)}/{len(combos)} corridas")
    summary.add_column("Run", justify="right", style="cyan")
    summary.add_column("Modelo")
    summary.add_column("num_ctx", justify="right")
    summary.add_column("kv_cache")
    for run_id, m, n, k in completed:
        summary.add_row(f"#{run_id}", m, str(n), k)
    console.print(summary)
    console.print(
        "[dim]Compara los runs en el Leaderboard o con "
        "`oly results show --run-id N` para cada uno.[/dim]"
    )


# ---------- results ----------

@results_app.command("show")
def results_show(
    run_id: int | None = typer.Option(None, "--run-id"),
    limit: int = typer.Option(10, "--limit"),
) -> None:
    """Muestra resumen del último run (o uno específico) con tabla de attempts."""
    with session_scope() as session:
        if run_id is None:
            run = session.scalar(select(Run).order_by(Run.id.desc()).limit(1))
            if run is None:
                console.print("[yellow]Sin corridas aún.[/yellow]")
                return
            run_id = run.id
        else:
            run = session.get(Run, run_id)
            if run is None:
                console.print(f"[red]Run #{run_id} no existe.[/red]")
                raise typer.Exit(1)

        console.print(
            Panel.fit(
                f"[bold]Run #{run.id}[/bold]\n"
                f"creado: {run.created_at}\n"
                f"status: {run.status}\n"
                f"notes: {run.notes or '-'}",
                border_style="cyan",
            )
        )

        attempts = session.scalars(
            select(Attempt).where(Attempt.run_id == run.id).order_by(Attempt.id)
        ).all()

        if not attempts:
            console.print("[dim]Sin attempts.[/dim]")
            return

        table = Table(show_lines=False)
        table.add_column("Modelo", style="cyan")
        table.add_column("Task", style="magenta")
        table.add_column("Try", justify="right")
        table.add_column("Status")
        table.add_column("tps", justify="right")
        table.add_column("ttft", justify="right")
        table.add_column("tok_in", justify="right")
        table.add_column("tok_out", justify="right")
        table.add_column("vram", justify="right")
        table.add_column("watts", justify="right")
        table.add_column("wall_s", justify="right")

        models_by_id = {m.id: m.name for m in session.scalars(select(Model)).all()}
        tasks_by_id = {t.id: t.task_id for t in session.scalars(select(TaskRow)).all()}

        successes = 0
        for a in attempts:
            status_style = {
                "success": "green",
                "fail": "yellow",
                "error": "red",
                "timeout": "red",
            }.get(a.status, "white")
            if a.status == "success":
                successes += 1
            table.add_row(
                models_by_id.get(a.model_id, "?"),
                tasks_by_id.get(a.task_id, "?"),
                str(a.try_n),
                f"[{status_style}]{a.status}[/{status_style}]",
                f"{a.tps_decode:.1f}" if a.tps_decode else "-",
                str(a.ttft_ms) if a.ttft_ms else "-",
                str(a.tokens_in) if a.tokens_in else "-",
                str(a.tokens_out) if a.tokens_out else "-",
                f"{a.peak_vram_mb}M" if a.peak_vram_mb else "-",
                f"{a.avg_watts:.1f}" if a.avg_watts else "-",
                f"{a.wall_time_s:.1f}" if a.wall_time_s else "-",
            )
        console.print(table)
        console.print(
            f"\n[bold]{successes}/{len(attempts)}[/bold] attempts exitosos"
        )


@results_app.command("list")
def results_list(limit: int = typer.Option(20, "--limit")) -> None:
    """Lista corridas recientes."""
    with session_scope() as session:
        runs = session.scalars(
            select(Run).order_by(Run.id.desc()).limit(limit)
        ).all()
        if not runs:
            console.print("[yellow]Sin corridas.[/yellow]")
            return
        table = Table(title="Corridas recientes")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Creada", style="dim")
        table.add_column("Status")
        table.add_column("Modelos")
        table.add_column("Suites")
        for r in runs:
            cfg = r.config_json or {}
            models_str = ", ".join(cfg.get("models", []))
            suites_str = ", ".join(cfg.get("suites", []))
            table.add_row(
                str(r.id), str(r.created_at)[:19], r.status, models_str, suites_str
            )
        console.print(table)


# ---------- serve ----------

@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Levanta el server FastAPI."""
    import uvicorn

    init_db()
    console.print(
        Panel.fit(
            f"[bold]Ollympics API[/bold]\n"
            f"http://{host}:{port}\n"
            f"docs: http://{host}:{port}/docs",
            border_style="green",
        )
    )
    uvicorn.run("ollympics.api.app:app", host=host, port=port, reload=reload)


# Silence Live import warning since it's optional usage above
_ = Live


if __name__ == "__main__":
    app()
