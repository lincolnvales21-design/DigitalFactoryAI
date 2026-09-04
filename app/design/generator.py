from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class DesignGenerator:

    def __init__(self):

        self.base_path = Path("generated_products")
        self.design_path = self.base_path / "design"

        self.design_path.mkdir(
            parents=True,
            exist_ok=True
        )

    def _get_font(self, size, bold=False):

        if bold:
            paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            ]
        else:
            paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            ]

        for path in paths:

            if Path(path).exists():

                return ImageFont.truetype(
                    path,
                    size
                )

        return ImageFont.load_default()

    def _wrap_text(
        self,
        draw,
        text,
        font,
        max_width
    ):

        words = text.split()
        lines = []
        current = ""

        for word in words:

            candidate = (
                current + " " + word
            ).strip()

            bbox = draw.textbbox(
                (0, 0),
                candidate,
                font=font
            )

            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:

                current = candidate

            else:

                if current:
                    lines.append(current)

                current = word

        if current:
            lines.append(current)

        return lines

    def create_cover(
        self,
        title,
        subtitle="Guia Prático para Pequenos Negócios",
        product_id=None
    ):

        width = 1600
        height = 2560

        image = Image.new(
            "RGB",
            (width, height),
            "#F7F4EE"
        )

        draw = ImageDraw.Draw(image)

        # ------------------------------------------
        # PAINEL PRINCIPAL
        # ------------------------------------------

        draw.rounded_rectangle(
            (85, 85, width - 85, height - 85),
            radius=45,
            fill="#FFFFFF"
        )

        # ------------------------------------------
        # FAIXA SUPERIOR
        # ------------------------------------------

        draw.rectangle(
            (85, 85, width - 85, 420),
            fill="#173F5F"
        )

        brand_font = self._get_font(
            42,
            bold=True
        )

        draw.text(
            (145, 190),
            "GUIA PRÁTICO",
            fill="#FFFFFF",
            font=brand_font
        )

        # ------------------------------------------
        # ELEMENTO VISUAL DE NEGÓCIOS
        # ------------------------------------------

        graph_left = 1050
        graph_top = 500

        draw.rounded_rectangle(
            (
                graph_left,
                graph_top,
                1430,
                850
            ),
            radius=30,
            fill="#E8F1F5"
        )

        draw.line(
            [
                (1100, 770),
                (1180, 700),
                (1260, 730),
                (1340, 610),
                (1400, 540)
            ],
            fill="#F28C28",
            width=18
        )

        draw.ellipse(
            (1380, 520, 1420, 560),
            fill="#F28C28"
        )

        # ------------------------------------------
        # TÍTULO
        # ------------------------------------------

        title_font = self._get_font(
            108,
            bold=True
        )

        title_lines = self._wrap_text(
            draw,
            title,
            title_font,
            1280
        )

        y = 570

        for line in title_lines:

            draw.text(
                (145, y),
                line,
                fill="#173F5F",
                font=title_font
            )

            y += 125

        # ------------------------------------------
        # SUBTÍTULO
        # ------------------------------------------

        subtitle_font = self._get_font(
            52
        )

        subtitle_lines = self._wrap_text(
            draw,
            subtitle,
            subtitle_font,
            1180
        )

        y += 55

        for line in subtitle_lines:

            draw.text(
                (150, y),
                line,
                fill="#52606D",
                font=subtitle_font
            )

            y += 72

        # ------------------------------------------
        # BLOCO DE BENEFÍCIO
        # ------------------------------------------

        benefit_top = 1420

        draw.rounded_rectangle(
            (
                145,
                benefit_top,
                1455,
                1735
            ),
            radius=35,
            fill="#FFF4E6"
        )

        benefit_title_font = self._get_font(
            40,
            bold=True
        )

        benefit_body_font = self._get_font(
            34
        )

        draw.text(
            (200, benefit_top + 55),
            "ORGANIZE • PLANEJE • VENDA",
            fill="#C45A00",
            font=benefit_title_font
        )

        benefit_text = (
            "Um guia direto para transformar "
            "a organização das vendas em ações práticas."
        )

        benefit_lines = self._wrap_text(
            draw,
            benefit_text,
            benefit_body_font,
            1160
        )

        text_y = benefit_top + 125

        for line in benefit_lines:

            draw.text(
                (200, text_y),
                line,
                fill="#5B4636",
                font=benefit_body_font
            )

            text_y += 52

        # ------------------------------------------
        # RODAPÉ
        # ------------------------------------------

        footer_font = self._get_font(
            38,
            bold=True
        )

        footer_small_font = self._get_font(
            30
        )

        draw.text(
            (150, 2240),
            "DigitalFactoryAI",
            fill="#173F5F",
            font=footer_font
        )

        draw.text(
            (150, 2300),
            "Conhecimento prático para negócios digitais",
            fill="#68737D",
            font=footer_small_font
        )

        # ------------------------------------------
        # DETALHE DECORATIVO
        # ------------------------------------------

        draw.rounded_rectangle(
            (
                1230,
                2180,
                1450,
                2245
            ),
            radius=25,
            fill="#F28C28"
        )

        draw.text(
            (1260, 2192),
            "EBOOK",
            fill="#FFFFFF",
            font=self._get_font(
                27,
                bold=True
            )
        )

        # ------------------------------------------
        # SALVAR
        # ------------------------------------------

        if product_id is not None:

            filename = (
                f"product_{product_id}_cover.png"
            )

        else:

            filename = "ebook_cover.png"

        output = self.design_path / filename

        image.save(
            output,
            "PNG",
            optimize=True
        )

        return {
            "status": "created",
            "type": "cover",
            "path": str(output),
            "message": "Capa comercial criada automaticamente."
        }


design_generator = DesignGenerator()
