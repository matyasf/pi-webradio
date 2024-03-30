
class TextBox:
    def __init__(self, xc:int, yc:int, width:int, height: int,
                 text:str, fontSize=25, hAlign='left',
                 line_spacing: float = 1, font: str = 'assets/static/PlayfairDisplay-Regular.otf'):
        self.xc = xc
        self.yc = yc
        self.width = width
        self.height = height
        self.text = text
        self.font_size = fontSize
        self.hAlign = hAlign # can be left, right, center, justify
        self.line_spacing = line_spacing
        self.font = font