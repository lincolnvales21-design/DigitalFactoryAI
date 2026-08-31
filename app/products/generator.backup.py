from pathlib import Path
from datetime import datetime


class ProductGenerator:


    def __init__(self):

        self.base_path = Path("generated_products")

        self.base_path.mkdir(
            exist_ok=True
        )


    def create_ebook(self, title: str, research=None):


        ebook_path = self.base_path / "ebook"

        ebook_path.mkdir(
            exist_ok=True
        )


        content = f"""
# {title}


## Introdução

Este ebook foi criado pelo DigitalFactoryAI.


## Capítulo 1 - Introdução ao tema

Conteúdo gerado automaticamente pelo ProductAgent.


## Capítulo 2 - Conceitos principais

Explicação dos fundamentos para iniciantes.


## Capítulo 3 - Aplicações práticas

Como utilizar esse conhecimento na prática.


## Conclusão

Material criado usando inteligência artificial.


Pesquisa utilizada:

{research}

Data:

{datetime.now()}
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

            "message": "Ebook criado pelo ProductGenerator."

        }



product_generator = ProductGenerator()
