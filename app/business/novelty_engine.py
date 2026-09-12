import json
import os
import re

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class NoveltyEngine:
    """
    Motor de novidade + validação comercial do DigitalFactoryAI.

    Atua antes da produção do produto.

    Decide se uma oportunidade:
      - deve ser descartada;
      - precisa de validação;
      - está pronta para produção.

    Não cria produto.
    Não publica.
    Não movimenta capital.
    """

    GENERIC_PATTERNS = [
        "ebook sobre produtividade",
        "ebook sobre finanças",
        "ebook sobre relacionamento",
        "ebook sobre marketing",
        "ebook sobre saúde",
        "ebook sobre bem estar",
        "guia sobre produtividade",
        "guia sobre finanças",
        "guia sobre relacionamento",
        "curso sobre produtividade",
        "curso sobre marketing",
        "curso sobre inteligência artificial",
        "melhorar sua vida",
        "ter mais sucesso",
        "ficar mais saudável",
        "ganhar dinheiro",
    ]

    MIN_READY_SCORE = 75
    MIN_VALIDATION_SCORE = 50

    # --------------------------------------------------------
    # UTILIDADES
    # --------------------------------------------------------

    @staticmethod
    def _normalize(value):
        if value is None:
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value).strip().lower()
        )

    def _text(self, opportunity):
        return self._normalize(
            " ".join(
                [
                    str(opportunity.get("area") or ""),
                    str(opportunity.get("problem") or ""),
                    str(opportunity.get("target_audience") or ""),
                    str(opportunity.get("recommended_format") or ""),
                    str(opportunity.get("market") or ""),
                    str(opportunity.get("commercial_thesis") or ""),
                    str(opportunity.get("differentiation_angle") or ""),
                ]
            )
        )

    # --------------------------------------------------------
    # SCORE LOCAL
    # --------------------------------------------------------

    def _local_score(self, opportunity):
        score = 0
        reasons = []

        area = opportunity.get("area")
        problem = opportunity.get("problem")
        audience = opportunity.get("target_audience")
        fmt = opportunity.get("recommended_format")
        market = opportunity.get("market")
        thesis = opportunity.get("commercial_thesis")
        differentiation = opportunity.get(
            "differentiation_angle"
        )

        if area:
            score += 10
        else:
            reasons.append("área ausente")

        if problem:
            score += 20

            problem_text = self._normalize(problem)

            if len(problem_text) >= 35:
                score += 10
            else:
                reasons.append("problema pouco específico")
        else:
            reasons.append("problema ausente")

        if audience:
            score += 15

            audience_text = self._normalize(audience)

            if len(audience_text) >= 20:
                score += 5
            else:
                reasons.append("público pouco específico")
        else:
            reasons.append("público ausente")

        if fmt:
            score += 10
        else:
            reasons.append("formato ausente")

        if market:
            score += 5
        else:
            reasons.append("mercado ausente")

        if thesis:
            score += 10
        else:
            reasons.append("tese comercial ausente")

        if differentiation:
            score += 15
        else:
            reasons.append("diferenciação ausente")

        text = self._text(opportunity)

        for pattern in self.GENERIC_PATTERNS:
            if self._normalize(pattern) in text:
                score -= 25
                reasons.append(
                    "padrão genérico detectado"
                )
                break

        return max(0, min(100, score)), reasons

    # --------------------------------------------------------
    # VALIDAÇÃO COMERCIAL
    # --------------------------------------------------------

    def _commercial_validation(self, opportunity, score):
        questions = []

        problem = opportunity.get("problem")
        audience = opportunity.get("target_audience")
        market = opportunity.get("market")

        if problem:
            questions.append(
                f"Existe demanda comprovável para o problema: "
                f"'{problem}'?"
            )
        else:
            questions.append(
                "Qual problema específico o produto resolve?"
            )

        if audience:
            questions.append(
                f"O público '{audience}' já procura ou paga "
                "por soluções semelhantes?"
            )
        else:
            questions.append(
                "Quem é o comprador específico?"
            )

        if market:
            questions.append(
                f"Quais canais permitem alcançar esse público "
                f"no mercado '{market}'?"
            )
        else:
            questions.append(
                "Qual mercado será atacado primeiro?"
            )

        questions.extend(
            [
                "Qual é a alternativa atual usada pelo cliente?",
                "Por que o cliente escolheria esta solução?",
                "Existe uma vantagem clara sobre alternativas existentes?",
                "Qual preço o público provavelmente aceita?",
                "Qual evidência mínima deve existir antes da produção?",
            ]
        )

        if score >= self.MIN_READY_SCORE:
            decision = "ready_for_product_creation"
            status = "ready"

        elif score >= self.MIN_VALIDATION_SCORE:
            decision = "requires_validation"
            status = "validation_required"

        else:
            decision = "reject"
            status = "rejected"

        return {
            "status": status,
            "decision": decision,
            "validation_questions": questions,
        }

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    def _fallback(self, opportunity):
        score, reasons = self._local_score(
            opportunity
        )

        validation = self._commercial_validation(
            opportunity,
            score,
        )

        return {
            "novelty_score": score,
            "commercial_score": score,
            "decision": validation["decision"],
            "status": validation["status"],
            "product_angle": (
                "Transformar tarefas administrativas "
                "repetitivas em fluxos simples de automação "
                "com inteligência artificial."
            ),
            "differentiation_strategy": (
                "Ensinar o cliente a identificar tarefas "
                "repetitivas, escolher quais automatizar, "
                "montar fluxos práticos e reutilizar os "
                "modelos no trabalho diário."
            ),
            "unique_mechanism": (
                "Sistema de Automação Administrativa por "
                "Fluxos: identificar, estruturar, automatizar "
                "e reutilizar tarefas administrativas com IA."
            ),
            "commercial_thesis": (
                opportunity.get(
                    "commercial_thesis"
                )
                or (
                    "Existe uma oportunidade potencial "
                    "quando um problema específico é "
                    "resolvido para um público claramente definido."
                )
            ),
            "validation_questions": validation[
                "validation_questions"
            ],
            "reasons": reasons,
        }

    # --------------------------------------------------------
    # ANÁLISE
    # --------------------------------------------------------

    async def analyze(self, opportunity):
        """
        Analisa novidade e força comercial.

        Usa IA externa quando disponível,
        mantendo fallback determinístico.
        """

        result = self._fallback(
            opportunity
        )

        api_key = os.getenv(
            "OPENAI_API_KEY"
        )

        if OpenAI and api_key:
            try:
                client = OpenAI(
                    api_key=api_key
                )

                prompt = f"""
Você é o motor de validação comercial
do DigitalFactoryAI.

Analise esta oportunidade:

{json.dumps(opportunity, ensure_ascii=False)}

Avalie de 0 a 100:

1. especificidade do problema;
2. clareza do comprador;
3. potencial de pagamento;
4. diferenciação;
5. clareza da tese comercial;
6. potencial do formato;
7. potencial do mercado;
8. risco de ser uma ideia genérica.

REGRAS:

- Não invente provas de demanda.
- Não invente clientes.
- Não invente vendas.
- Não afirme que existe demanda comprovada sem evidência.
- Não prometa resultados.
- Não considere uma ideia boa apenas porque parece interessante.

Classificação:

75-100:
ready_for_product_creation

50-74:
requires_validation

0-49:
reject

Retorne SOMENTE JSON com:

novelty_score
commercial_score
decision
product_angle
differentiation_strategy
unique_mechanism
commercial_thesis
validation_questions
reasons
"""

                response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Você é um analista "
                                "comercial rigoroso."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.2,
                )

                text = (
                    response
                    .choices[0]
                    .message
                    .content
                    .strip()
                )

                generated = json.loads(
                    text
                )

                if isinstance(
                    generated,
                    dict
                ):
                    result.update(
                        generated
                    )

            except Exception:
                # Fallback continua sendo a autoridade
                # mínima para manter o sistema operacional.
                pass

        return result

    # --------------------------------------------------------
    # COMPATIBILIDADE
    # --------------------------------------------------------

    async def evaluate(self, opportunity):
        """
        Alias mantido para compatibilidade
        com o AutonomousBusinessEngine.
        """

        return await self.analyze(
            opportunity
        )


novelty_engine = NoveltyEngine()
