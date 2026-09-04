import re


class PricingEngine:

    def calculate(self, research: dict, task: str = "") -> dict:
        """
        Calcula um preço inicial a partir da faixa sugerida
        pelo ResearchAgent.

        O preço é uma hipótese inicial e deve ser validado
        com vendas reais.
        """

        suggested_price = str(
            research.get("suggested_price", "")
        )

        # --------------------------------------------------
        # MERCADO DEFINIDO PELO RADAR
        # --------------------------------------------------

        market = str(
            research.get("market", "")
        ).strip().lower()

        international_markets = {
            "internacional",
            "mercado internacional",
            "international",
            "eua",
            "estados unidos",
            "usa",
            "us",
            "global",
        }

        is_international = (
            market in international_markets
            or "internacional" in market
            or "international" in market
        )

        # --------------------------------------------------
        # Procurar faixas em BRL
        # --------------------------------------------------

        brl_ranges = re.findall(
            r"R\$\s*([\d.,]+)\s*(?:a|-|até)\s*R?\$?\s*([\d.,]+)",
            suggested_price,
            flags=re.IGNORECASE
        )

        # --------------------------------------------------
        # Procurar faixas em USD
        # --------------------------------------------------

        usd_ranges = re.findall(
            r"US\$\s*([\d.,]+)\s*(?:a|-|até)\s*US?\$?\s*([\d.,]+)",
            suggested_price,
            flags=re.IGNORECASE
        )

        # --------------------------------------------------
        # Converter número brasileiro
        # --------------------------------------------------

        def parse_number(value: str) -> float:

            value = value.strip()

            # Exemplo: 1.299,90
            if "," in value and "." in value:
                value = value.replace(".", "")
                value = value.replace(",", ".")

            # Exemplo: 49,90
            elif "," in value:
                value = value.replace(",", ".")

            return float(value)

        # --------------------------------------------------
        # Mercado internacional
        # --------------------------------------------------

        if is_international and usd_ranges:

            minimum = parse_number(
                usd_ranges[0][0]
            )

            maximum = parse_number(
                usd_ranges[0][1]
            )

            price = round(
                (minimum + maximum) / 2,
                2
            )

            return {
                "price": price,
                "currency": "USD",
                "minimum": minimum,
                "maximum": maximum,
                "source": "research_suggested_price_international",
                "reason": (
                    "Mercado internacional priorizado pelo Radar "
                    "e faixa internacional identificada."
                )
            }

        # --------------------------------------------------
        # Brasil
        # --------------------------------------------------

        if brl_ranges and not is_international:

            minimum = parse_number(
                brl_ranges[0][0]
            )

            maximum = parse_number(
                brl_ranges[0][1]
            )

            price = round(
                (minimum + maximum) / 2,
                2
            )

            return {
                "price": price,
                "currency": "BRL",
                "minimum": minimum,
                "maximum": maximum,
                "source": "research_suggested_price",
                "reason": (
                    "Preço inicial calculado no ponto médio "
                    "da faixa sugerida pela pesquisa."
                )
            }

        # --------------------------------------------------
        # Internacional
        # --------------------------------------------------

        if is_international and not usd_ranges:

            return {
                "price": 19.90,
                "currency": "USD",
                "minimum": 9.90,
                "maximum": 29.90,
                "source": "international_default",
                "reason": (
                    "Mercado internacional definido pelo Radar. "
                    "Como a pesquisa não forneceu faixa em USD, "
                    "foi aplicada uma faixa inicial internacional."
                )
            }

        if usd_ranges:

            minimum = parse_number(
                usd_ranges[0][0]
            )

            maximum = parse_number(
                usd_ranges[0][1]
            )

            price = round(
                (minimum + maximum) / 2,
                2
            )

            return {
                "price": price,
                "currency": "USD",
                "minimum": minimum,
                "maximum": maximum,
                "source": "research_suggested_price",
                "reason": (
                    "Preço inicial calculado no ponto médio "
                    "da faixa sugerida pela pesquisa."
                )
            }

        # --------------------------------------------------
        # Segurança
        # --------------------------------------------------

        raise ValueError(
            "Não foi possível interpretar a faixa de preço "
            "fornecida pelo ResearchAgent."
        )
