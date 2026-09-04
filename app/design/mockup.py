from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


class MockupGenerator:

    def __init__(self):
        self.base_path = Path("generated_products")
        self.design_path = self.base_path / "design"

        self.design_path.mkdir(
            parents=True,
            exist_ok=True
        )

    def create_ebook_mockup(self, product_id):

        cover_path = (
            self.design_path /
            f"product_{product_id}_cover.png"
        )

        if not cover_path.exists():
            raise FileNotFoundError(
                f"Capa não encontrada: {cover_path}"
            )

        cover = Image.open(
            cover_path
        ).convert("RGBA")

        # ------------------------------------------
        # TAMANHO DO MOCKUP
        # ------------------------------------------

        width = 1800
        height = 1200

        canvas = Image.new(
            "RGBA",
            (width, height),
            "#F4F1EA"
        )

        # ------------------------------------------
        # SOMBRA
        # ------------------------------------------

        shadow = Image.new(
            "RGBA",
            (900, 950),
            (0, 0, 0, 0)
        )

        shadow_draw = ImageDraw.Draw(
            shadow
        )

        shadow_draw.rounded_rectangle(
            (80, 80, 820, 900),
            radius=35,
            fill=(0, 0, 0, 90)
        )

        shadow = shadow.filter(
            ImageFilter.GaussianBlur(35)
        )

        canvas.alpha_composite(
            shadow,
            (390, 180)
        )

        # ------------------------------------------
        # REDIMENSIONAR CAPA
        # ------------------------------------------

        book_height = 850

        ratio = (
            book_height /
            cover.height
        )

        book_width = int(
            cover.width * ratio
        )

        book = cover.resize(
            (book_width, book_height),
            Image.Resampling.LANCZOS
        )

        # ------------------------------------------
        # EFEITO DE LIVRO
        # ------------------------------------------

        book_layer = Image.new(
            "RGBA",
            (
                book_width + 70,
                book_height + 70
            ),
            (0, 0, 0, 0)
        )

        layer_draw = ImageDraw.Draw(
            book_layer
        )

        # lombada visual

        layer_draw.rounded_rectangle(
            (
                25,
                25,
                book_width + 45,
                book_height + 45
            ),
            radius=25,
            fill=(220, 220, 220, 255)
        )

        book_layer.alpha_composite(
            book,
            (25, 25)
        )

        # ------------------------------------------
        # LEVE INCLINAÇÃO
        # ------------------------------------------

        book_layer = book_layer.rotate(
            6,
            expand=True,
            resample=Image.Resampling.BICUBIC
        )

        # ------------------------------------------
        # POSICIONAR LIVRO
        # ------------------------------------------

        x = 330
        y = 150

        canvas.alpha_composite(
            book_layer,
            (x, y)
        )

        # ------------------------------------------
        # SEGUNDO ELEMENTO: MINI LIVRO
        # ------------------------------------------

        mini_height = 560

        ratio2 = (
            mini_height /
            cover.height
        )

        mini_width = int(
            cover.width * ratio2
        )

        mini = cover.resize(
            (mini_width, mini_height),
            Image.Resampling.LANCZOS
        )

        mini_layer = Image.new(
            "RGBA",
            (
                mini_width + 40,
                mini_height + 40
            ),
            (0, 0, 0, 0)
        )

        mini_layer.alpha_composite(
            mini,
            (20, 20)
        )

        mini_layer = mini_layer.rotate(
            -8,
            expand=True,
            resample=Image.Resampling.BICUBIC
        )

        canvas.alpha_composite(
            mini_layer,
            (1080, 470)
        )

        # ------------------------------------------
        # TEXTO PROMOCIONAL
        # ------------------------------------------

        draw = ImageDraw.Draw(
            canvas
        )

        font_path = (
            "/usr/share/fonts/truetype/"
            "dejavu/DejaVuSans-Bold.ttf"
        )

        regular_path = (
            "/usr/share/fonts/truetype/"
            "dejavu/DejaVuSans.ttf"
        )

        try:

            title_font = ImageFont.truetype(
                font_path,
                64
            )

            body_font = ImageFont.truetype(
                regular_path,
                34
            )

        except Exception:

            title_font = None
            body_font = None

        draw.text(
            (1050, 150),
            "Como Organizar suas",
            fill="#173F5F",
            font=title_font
        )

        draw.text(
            (1050, 225),
            "Vendas Online",
            fill="#173F5F",
            font=title_font
        )

        draw.text(
            (1050, 330),
            "Guia prático para pequenos negócios",
            fill="#52606D",
            font=body_font
        )

        # ------------------------------------------
        # ETIQUETA
        # ------------------------------------------

        draw.rounded_rectangle(
            (
                1050,
                780,
                1510,
                850
            ),
            radius=25,
            fill="#F28C28"
        )

        draw.text(
            (1170, 795),
            "EBOOK",
            fill="#FFFFFF",
            font=body_font
        )

        # ------------------------------------------
        # SALVAR
        # ------------------------------------------

        output = (
            self.design_path /
            f"product_{product_id}_mockup.png"
        )

        canvas.convert(
            "RGB"
        ).save(
            output,
            "PNG",
            optimize=True
        )

        return {
            "status": "created",
            "type": "ebook_mockup",
            "path": str(output),
            "message": "Mockup promocional criado automaticamente."
        }


mockup_generator = MockupGenerator()
