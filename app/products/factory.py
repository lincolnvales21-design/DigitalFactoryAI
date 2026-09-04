import json
from datetime import datetime, timezone
from pathlib import Path


class ProductFactory:
    """
    Fábrica de produtos do DigitalFactoryAI.

    Decide o formato do produto com base na oportunidade,
    problema, público e tese de diferenciação.

    Antes de produzir, respeita o Quality Gate do Novelty Engine.

    A fábrica mantém compatibilidade com o gerador de ebook
    existente e cria artefatos estruturados para os demais formatos.

    Não movimenta capital.
    Não executa pagamentos.
    """

    FORMAT_ALIASES = {
        "ebook": "ebook",
        "livro": "ebook",
        "guia": "guide",
        "guia prático": "guide",
        "checklist": "checklist",
        "planner": "planner",
        "template": "template",
        "kit digital": "kit",
        "curso": "course",
        "curso curto": "course",
        "ferramenta digital": "tool",
        "diagnóstico": "diagnostic",
        "diagnostico": "diagnostic",
    }

    FORMAT_DESCRIPTIONS = {
        "ebook": "Ebook estruturado e orientado à resolução do problema.",
        "guide": "Guia prático com execução passo a passo.",
        "checklist": "Checklist operacional para execução rápida.",
        "planner": "Planner estruturado para acompanhamento e execução.",
        "template": "Template reutilizável para acelerar uma tarefa.",
        "kit": "Kit digital com múltiplos recursos complementares.",
        "course": "Curso curto dividido em módulos práticos.",
        "tool": "Ferramenta digital orientada a uma tarefa específica.",
        "diagnostic": "Diagnóstico estruturado com avaliação e recomendações.",
    }

    READY_DECISIONS = {
        "ready_for_product_creation",
    }

    BLOCKED_DECISIONS = {
        "requires_validation",
        "reject",
    }

    # --------------------------------------------------------
    # FORMATO
    # --------------------------------------------------------

    def normalize_format(self, value):
        if not value:
            return "ebook"

        import unicodedata

        value = str(value).strip().lower()

        # Remove acentos para garantir que:
        # diagnóstico == diagnostico
        normalized = unicodedata.normalize(
            "NFKD",
            value,
        ).encode(
            "ascii",
            "ignore",
        ).decode(
            "ascii",
        )

        aliases = {
            "ebook": "ebook",
            "livro": "ebook",

            "guia": "guide",
            "guia pratico": "guide",

            "checklist": "checklist",
            "planner": "planner",
            "template": "template",

            "kit": "kit",
            "kit digital": "kit",

            "curso": "course",
            "curso curto": "course",
            "course": "course",

            "ferramenta": "tool",
            "ferramenta digital": "tool",
            "tool": "tool",

            "diagnostico": "diagnostic",
            "diagnostic": "diagnostic",
        }

        return aliases.get(
            normalized,
            self.FORMAT_ALIASES.get(
                value,
                "ebook",
            ),
        )

    def choose_format(self, research=None, novelty=None):
        research = research or {}
        novelty = novelty or {}

        recommended = (
            novelty.get("recommended_format")
            or research.get("recommended_format")
            or research.get("format")
        )

        if recommended:
            return self.normalize_format(
                recommended
            )

        problem = str(
            research.get("problem", "")
        ).lower()

        if "organizar" in problem:
            return "planner"

        if (
            "processo" in problem
            or "processos" in problem
        ):
            return "template"

        if (
            "avaliar" in problem
            or "diagnóstico" in problem
            or "diagnostico" in problem
        ):
            return "diagnostic"

        return "ebook"

    # --------------------------------------------------------
    # QUALITY GATE
    # --------------------------------------------------------

    def validate_production_gate(self, novelty=None):
        """
        Verifica se a oportunidade foi aprovada
        pelo Novelty Engine antes da produção.

        Produção só é autorizada quando:
            decision == ready_for_product_creation
        """

        novelty = novelty or {}

        decision = (
            novelty.get("decision")
            or novelty.get("status")
        )

        if decision in self.READY_DECISIONS:
            return {
                "allowed": True,
                "decision": decision,
                "reason": (
                    "Oportunidade aprovada pelo "
                    "Quality Gate comercial."
                ),
            }

        if decision in self.BLOCKED_DECISIONS:
            return {
                "allowed": False,
                "decision": decision,
                "reason": (
                    "Oportunidade não está autorizada "
                    "para produção."
                ),
            }

        return {
            "allowed": False,
            "decision": decision,
            "reason": (
                "Decisão comercial ausente. "
                "Produção bloqueada por segurança."
            ),
        }

    # --------------------------------------------------------
    # TÍTULO
    # --------------------------------------------------------

    def build_title(
        self,
        research,
        novelty,
        product_format,
        product_title=None,
    ):
        # Se o ProductAgent já definiu um nome comercial,
        # a Factory deve preservar exatamente esse nome.
        if product_title:
            return str(product_title).strip()
        area = (
            research.get("niche")
            or research.get("area")
            or novelty.get("area")
            or "Solução Digital"
        )

        mechanism = (
            novelty.get("unique_mechanism")
            or "Método Prático"
        )

        mechanism = str(
            mechanism
        ).strip()

        if len(mechanism) > 80:
            mechanism = (
                mechanism[:80].rstrip()
                + "..."
            )

        names = {
            "ebook": (
                f"Método Prático de {area.title()}"
            ),
            "guide": (
                f"Guia de Execução — {area.title()}"
            ),
            "checklist": (
                f"Checklist de {area.title()}"
            ),
            "planner": (
                f"Planner de {area.title()}"
            ),
            "template": (
                f"Kit de Templates — {area.title()}"
            ),
            "kit": (
                f"Kit Prático de {area.title()}"
            ),
            "course": (
                f"Curso Prático de {area.title()}"
            ),
            "tool": (
                f"Ferramenta Inteligente — {area.title()}"
            ),
            "diagnostic": (
                f"Diagnóstico de {area.title()}"
            ),
        }

        return names.get(
            product_format,
            f"Solução Prática de {area.title()}",
        )

    # --------------------------------------------------------
    # DESCRIÇÃO
    # --------------------------------------------------------

    def build_description(
        self,
        research,
        novelty,
        product_format,
    ):
        problem = research.get(
            "problem",
            "resolver um problema específico",
        )

        audience = research.get(
            "target_audience",
            "pessoas interessadas na solução",
        )

        angle = novelty.get(
            "product_angle",
            "",
        )

        differentiation = novelty.get(
            "differentiation_strategy",
            "",
        )

        # Limpa pontuação e espaços para evitar
        # duplicações vindas dos motores anteriores.
        problem = str(problem).strip().rstrip(".")
        audience = str(audience).strip().rstrip(".")
        angle = str(angle).strip().rstrip(".")
        differentiation = str(differentiation).strip().rstrip(".")

        format_description = self.FORMAT_DESCRIPTIONS.get(
            product_format,
            product_format,
        )

        parts = [
            (
                f"Solução prática para {audience}, "
                f"focada em {problem}."
            ),
        ]

        if angle and angle.lower() not in parts[0].lower():
            parts.append(f"Ângulo: {angle}.")

        if (
            differentiation
            and differentiation.lower() not in angle.lower()
        ):
            parts.append(
                f"Diferencial: {differentiation}."
            )

        parts.append(
            f"Formato: {format_description}"
        )

        return " ".join(parts).strip()

    # --------------------------------------------------------
    # MARKDOWN
    # --------------------------------------------------------

    def build_markdown(
        self,
        title,
        description,
        research,
        novelty,
        product_format,
    ):
        problem = research.get(
            "problem",
            "",
        )

        audience = research.get(
            "target_audience",
            "",
        )

        opportunity = research.get(
            "opportunity",
            "",
        )

        mechanism = novelty.get(
            "unique_mechanism",
            "",
        )

        differentiation = novelty.get(
            "differentiation_strategy",
            "",
        )

        thesis = novelty.get(
            "commercial_thesis",
            "",
        )

        product_angle = novelty.get(
            "product_angle",
            "",
        )

        sections = [
            f"# {title}",
            "",
            description,
            "",
            "## Para quem é",
            "",
            str(audience),
            "",
            "## Problema resolvido",
            "",
            str(problem),
            "",
            "## Método",
            "",
            str(mechanism),
            "",
            "## Diferencial",
            "",
            str(differentiation),
            "",
            "## Tese comercial",
            "",
            str(thesis),
            "",
            "## Ângulo do produto",
            "",
            str(product_angle),
            "",
            "## Oportunidade",
            "",
            str(opportunity),
            "",
            "## Diagnóstico inicial",
            "",
            (
                "Comece identificando a situação atual relacionada ao "
                f"problema: {problem}"
            ),
            "",
            "Perguntas para o diagnóstico:",
            "",
            f"- Qual é a principal dificuldade em: {problem}?",
            f"- Quem enfrenta esse problema: {audience}?",
            "- O que já foi tentado?",
            "- Qual resultado seria considerado uma melhoria?",
            "",
            "## Como usar",
            "",
            "1. Faça o diagnóstico inicial.",
            "2. Escolha a prioridade mais importante.",
            "3. Aplique o método em pequenas etapas.",
            "4. Registre o que aconteceu.",
            "5. Ajuste a estratégia conforme os resultados.",
            "",
            "## Aplicação prática",
            "",
            "### Ação 1 — Diagnosticar",
            "",
            f"Descreva a situação atual relacionada a: {problem}.",
            "",
            "### Ação 2 — Aplicar o método",
            "",
            f"Use o método definido para este produto: {mechanism}.",
            "",
            "### Ação 3 — Diferenciar a abordagem",
            "",
            f"Observe o diferencial proposto: {differentiation}.",
            "",
            "### Ação 4 — Executar",
            "",
            "Aplique uma mudança por vez e registre o resultado.",
            "",
            "## Checklist de aplicação",
            "",
            "- [ ] Diagnóstico realizado",
            "- [ ] Prioridade definida",
            "- [ ] Método aplicado",
            "- [ ] Resultado registrado",
            "- [ ] Próximo ajuste definido",
            "",
            "## Plano de execução",
            "",
            "- Etapa 1 — Diagnóstico",
            "- Etapa 2 — Priorização",
            "- Etapa 3 — Aplicação do método",
            "- Etapa 4 — Medição",
            "- Etapa 5 — Ajustes",
            "",
            "## Medição e ajustes",
            "",
            "Registre antes e depois da aplicação para identificar "
            "o que melhorou, o que não funcionou e qual deve ser "
            "o próximo ajuste.",
            "",
            f"**Formato:** {product_format}",
            "",
            (
                "**Validação comercial:** "
                "aprovada antes da produção."
            ),
            "",
            (
                "Gerado pelo DigitalFactoryAI em "
                f"{datetime.now(timezone.utc).isoformat()}"
            ),
        ]

        return "\n".join(
            sections
        )

    # --------------------------------------------------------
    # ARTEFATO
    # --------------------------------------------------------

    def create_artifact(
        self,
        product_id,
        research,
        novelty=None,
        product_format=None,
    ):
        research = research or {}
        novelty = novelty or {}

        # =====================================================
        # QUALITY GATE — PRIMEIRA BARREIRA
        # =====================================================

        gate = self.validate_production_gate(
            novelty
        )

        if not gate["allowed"]:
            return {
                "status": "blocked",
                "product_id": product_id,
                "reason": gate["reason"],
                "decision": gate["decision"],
                "artifact": None,
            }

        # =====================================================
        # FORMATO
        # =====================================================

        product_format = (
            product_format
            or self.choose_format(
                research,
                novelty,
            )
        )

        product_format = self.normalize_format(
            product_format
        )

        # =====================================================
        # CONTEÚDO
        # =====================================================

        title = self.build_title(
            research,
            novelty,
            product_format,
            product_title=research.get("product_title"),
        )

        description = self.build_description(
            research,
            novelty,
            product_format,
        )

        markdown = self.build_markdown(
            title,
            description,
            research,
            novelty,
            product_format,
        )

        # =====================================================
        # ARTEFATO → DIRETÓRIO DE ENTREGA
        # =====================================================

        if product_format == "ebook":
            output_dir = Path(
                "generated_products/ebook"
            )
        else:
            output_dir = (
                Path("generated_products")
                / product_format
            )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = (
            output_dir
            / f"product_{product_id}.md"
        )

        path.write_text(
            markdown,
            encoding="utf-8",
        )

        return {
            "status": "success",
            "product_id": product_id,
            "title": title,
            "description": description,
            "product_type": product_format,
            "format": product_format,
            "artifact": str(path),
            "quality_gate": {
                "status": "approved",
                "decision": gate["decision"],
            },
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }


product_factory = ProductFactory()
