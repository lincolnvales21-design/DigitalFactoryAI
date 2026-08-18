from pathlib import Path
from datetime import datetime


class ProductGenerator:

    def __init__(self):

        self.base_path = Path("generated_products")

        self.base_path.mkdir(
            exist_ok=True
        )

    def _research_text(self, research):

        if not research:
            return "Nenhuma pesquisa disponível."

        if isinstance(research, dict):

            parts = []

            for key, value in research.items():

                parts.append(
                    f"{key}: {value}"
                )

            return "\n".join(parts)

        return str(research)

    def create_ebook(
        self,
        title: str,
        research=None
    ):

        ebook_path = self.base_path / "ebook"

        ebook_path.mkdir(
            exist_ok=True
        )

        research_text = self._research_text(
            research
        )

        content = f"""# {title}

## Guia Prático

### Produto criado pelo DigitalFactoryAI

Este material foi desenvolvido a partir de uma análise de mercado realizada pelo sistema DigitalFactoryAI.

O objetivo deste ebook é transformar uma oportunidade identificada na pesquisa em um guia prático e aplicável.

---

## Introdução

Encontrar uma oportunidade de mercado é apenas o primeiro passo.

Uma oportunidade precisa ser transformada em uma solução clara, simples e útil para um público específico.

Este ebook apresenta uma abordagem prática para compreender a oportunidade identificada e transformar conhecimento em ação.

---

## Capítulo 1 — Entendendo a oportunidade

A primeira etapa é compreender o problema que existe no mercado.

Uma boa oportunidade normalmente surge quando existe uma combinação entre:

- uma necessidade real;
- pessoas procurando uma solução;
- dificuldade para encontrar respostas;
- possibilidade de oferecer uma solução simples;
- disposição do público para investir nessa solução.

A pesquisa utilizada pelo DigitalFactoryAI serviu como ponto de partida para identificar essa oportunidade.

### Insight da pesquisa

{research_text}

---

## Capítulo 2 — Definindo o público

Uma solução comercial precisa ter um público claramente definido.

Para isso, considere:

1. Quem possui o problema?
2. Qual é a principal dificuldade dessa pessoa?
3. O que ela já tentou fazer?
4. Qual resultado ela deseja alcançar?
5. Por que ela pagaria por uma solução?

Quanto mais específico for o público, mais fácil será criar uma comunicação comercial relevante.

---

## Capítulo 3 — Transformando conhecimento em solução

Uma oportunidade pode ser transformada em produto quando o conhecimento é organizado de maneira prática.

Uma boa solução deve:

- explicar o problema;
- apresentar uma metodologia;
- fornecer exemplos;
- oferecer passos concretos;
- facilitar a execução;
- ajudar o comprador a alcançar um resultado.

O objetivo não é simplesmente entregar informação.

O objetivo é ajudar o cliente a chegar a um resultado.

---

## Capítulo 4 — Plano de ação

Utilize este processo para transformar a oportunidade em ação:

### Passo 1

Defina claramente o problema que será resolvido.

### Passo 2

Escolha um público específico.

### Passo 3

Defina o resultado que o cliente deseja alcançar.

### Passo 4

Organize o conhecimento necessário para alcançar esse resultado.

### Passo 5

Transforme o conhecimento em passos simples.

### Passo 6

Execute, avalie os resultados e faça melhorias.

---

## Capítulo 5 — Checklist prático

Antes de lançar uma solução, verifique:

- [ ] O problema está claramente definido?
- [ ] O público está claramente definido?
- [ ] Existe uma promessa de resultado?
- [ ] O conteúdo é realmente útil?
- [ ] Existem passos práticos?
- [ ] O material pode ser consumido facilmente?
- [ ] A oferta possui um preço definido?
- [ ] Existe um canal de venda?
- [ ] Existe uma forma de receber pagamentos?
- [ ] Existe uma estratégia de divulgação?

---

## Conclusão

Uma oportunidade de mercado só se transforma em negócio quando existe uma solução que alguém considera valiosa.

O DigitalFactoryAI foi projetado para automatizar esse processo:

**pesquisar → identificar oportunidade → criar produto → divulgar → vender → analisar resultados → melhorar.**

Este ebook representa uma primeira versão do produto criado automaticamente pela plataforma.

O próximo estágio é validar a oferta com clientes reais e utilizar os resultados para melhorar continuamente o produto.

---

## Pesquisa utilizada

{research_text}

---

## Informações do produto

**Gerado por:** DigitalFactoryAI  
**Tipo:** Ebook  
**Data de geração:** {datetime.now().isoformat()}

"""

        file = ebook_path / "ebook_final.md"

        file.write_text(
            content,
            encoding="utf-8"
        )

        return {

            "status": "created",

            "type": "ebook",

            "path": str(file),

            "message": "Ebook comercial criado pelo ProductGenerator."

        }


product_generator = ProductGenerator()
