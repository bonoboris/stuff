"""Script to generate a HTML file with a Desmos embedded graph representing the scoring system."""

from typing import List, Optional, Tuple
import json
import dataclasses
from collections import abc
import itertools

REPLACE_MAP = {
    "(": r"\left(",
    ")": r"\right)",
    " ": r"\ ",
    "*": r"\cdot ",
    "<=":"\le ",
    ">=":"\ge ",
}

DERIVATE = "\\frac{d}{dx}"
BLACK = "#000000"
COLORS = ('#c74440','#2d70b3', '#388c46', '#6042a6','#fa7e19','#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000')
COLOR_GEN = itertools.cycle(COLORS)

def replace(formula:str):
    for pattern, sub in REPLACE_MAP.items():
        formula = formula.replace(pattern, sub)
    return formula

def frac(num:str, den:str):
    return f"\\frac{{{num}}}{{{den}}}"

def power(base:str, exp:str):
    return f"{base}^{{{exp}}}"


class NamedThingy:
    @dataclasses.dataclass
    class ValRange:
        val: float
        min: float
        max: float
    
    def __init__(self, prefix:str, suffix:str, c_vals: Optional[Tuple[float, ...]] = None, m_vals: Optional[Tuple[float, ...]] = None, color:Optional[str] = None):
        self.prefix: str = prefix
        self.suffix: str = suffix
        self.color = color or next(COLOR_GEN)
        self.c_vals = self.ValRange(1, 0, 10)
        if isinstance(c_vals, (int, float)):
            self.c_vals = self.ValRange(c_vals, 0, 10)
        elif isinstance(c_vals, self.ValRange):
            self.c_vals = c_vals
        elif isinstance(c_vals, abc.Iterable):
            self.c_vals = self.ValRange(*c_vals)
        self.m_vals = self.ValRange(1, 0, 10)
        if isinstance(m_vals, (int, float)):
            self.m_vals = self.ValRange(m_vals, 0, 100)
        elif isinstance(m_vals, self.ValRange):
            self.m_vals = m_vals
        elif isinstance(m_vals, abc.Iterable):
            self.m_vals = self.ValRange(*m_vals)
    
    @property
    def full(self):
        return self.prefix + self.suffix.capitalize()

    @property
    def x(self):
        return f"x_{{{self.suffix}}}"
    
    @property
    def c(self):
        return f"c_{{{self.full}}}"
    
    @property
    def m(self):
        return f"m_{{{self.full}}}"
    
    @property
    def f(self):
        return f"f_{{{self.full}}}"

    @property
    def g(self):
        return f"g_{{{self.full}}}"

    @property
    def d(self):
        return f"d_{{{self.full}}}"

    @property
    def s(self):
        return f"s_{{{self.full}}}"
    
    def any_suffix(self, base):
        return f"{base}_{{{self.prefix}}}"

    def any_full(self, base):
        return f"{base}_{{{self.full}}}"

def make_restriction(name: NamedThingy):
    return replace(f"\\left\\{{{name.m_vals.min}<=x<={name.m_vals.max}\\right\\}}")

def make_ari_rexpr(*names: NamedThingy):
    num = replace("+".join(f"{name.x}*{name.c}" for name in names))
    den = replace("+".join(name.c for name in names))
    return frac(num, den)

def make_geo_rexpr(*names: NamedThingy):
    base = replace("(" + "*".join(power(name.x, name.c) for name in names) + ")")
    exp = frac("1", replace("+".join(name.c for name in names)))
    return power(base, exp)

def make_x_params(*names: NamedThingy):
    inside = ", ".join(name.x for name in names)
    return replace(f"({inside})")

def make_m_params(*names: NamedThingy, as_x:Optional[NamedThingy] = None):
    inside = ", ".join(name.m if name != as_x else "x" for name in names)
    return replace(f"({inside})")

def make_func_lexpr(funcname: NamedThingy, *varnames: NamedThingy):
    return f"{funcname.s}{make_x_params(*varnames)}"

def make_graph_expr(graphname: NamedThingy, funcname:NamedThingy, *varnames: NamedThingy):
    return graphname.g + replace("(x)=") +f"{funcname.s}{make_m_params(*varnames, as_x=graphname)}{make_restriction(graphname)}"

def make_json(score_val, measures_vals):
    score = NamedThingy(score_val, "", color=BLACK)
    score_geo = NamedThingy(score_val, "geo", color=BLACK)
    score_ari = NamedThingy(score_val, "ari", color=BLACK)
    variables: List[NamedThingy] = []
    for elt in measures_vals:
        if isinstance(elt, str):
            variables.append(NamedThingy(score_val, elt))
        elif isinstance(elt, abc.Sequence):
            variables.append(NamedThingy(score_val, *elt))
    exprs = [
        # Formula expr
        {
            "id": f"{score_val}FormulaPointer",
            "type": "expression",
            "latex": f"{make_func_lexpr(score, *variables)}={make_func_lexpr(score_ari, *variables)}",
            "hidden": True,
        },
        # Ari exrp
        {
            "id": f"{score_val}FormulaAri",
            "type": "expression",
            "latex": f"{make_func_lexpr(score_ari, *variables)}={make_ari_rexpr(*variables)}",
            "hidden": True,
        },
        # Ari exrp
        {
            "id": f"{score_val}FormulaGeo",
            "type": "expression",
            "latex": f"{make_func_lexpr(score_geo, *variables)}={make_geo_rexpr(*variables)}",
            "hidden": True,
        },
    ]
    for var in variables:
        print(make_restriction(var))
        exprs.extend(
            [
                # Measure slider
                {
                    "id": f"{var.full}MeasSlider",
                    "type":"expression",
                    "latex": f"{var.m}={var.m_vals.val}",
                    "sliderBounds": {"min": f"{var.m_vals.min}", "max":f"{var.m_vals.max}"},
                },
                # Coef slider
                {
                    "id": f"{var.full}CoefSlider",
                    "type":"expression",
                    "latex": f"{var.c}={var.c_vals.val}",
                    "sliderBounds": {"min": f"{var.c_vals.min}", "max":f"{var.c_vals.max}"},
                },
                # Partial Graph
                {
                    "id": f"{var.full}Graph",
                    "type": "expression",
                    "latex": make_graph_expr(var, score, *variables),
                    "color": var.color,
                },
                # Partial point
                {
                    "id": f"{var.full}GraphPoint",
                    "type": "expression",
                    "latex": replace(f"({var.m}, {var.g}({var.m}))"),
                    "label": var.suffix.capitalize(),
                    "showLabel": True,
                    "color": var.color,
                },
                # PartialDerivateGraph
                {
                    "id": f"{var.full}DerivateGraph",
                    "type": "expression",
                    "latex": replace(f"{var.d}(x)={DERIVATE}({var.g}(x))"),
                    "color": var.color,
                    "style": "DASHED"
                },
                # Partial point
                {
                    "id": f"{var.full}DerivateGraphPoint",
                    "type": "expression",
                    "latex": replace(f"({var.m}, {var.d}({var.m}))"),
                    "label": "",
                    "showLabel": True,
                    "color": var.color,
                },
            ]
        )
    return exprs

if __name__ == "__main__":
    score = "mobility"
    measures = [
        ("call", 1, 15),
        ("gps", 2, 7),
        ("camera", 8, 4),
        ("sn", 4, 9),
        ("runtastic", 2, 30)
    ]
    exprs_json_string = json.dumps(make_json(score, measures), indent=None)
    with open("desmosTemplate.html", "r", encoding="utf8") as templateFile:
        htmlTemplate = templateFile.read()
    dst_content = htmlTemplate.replace("{{EXPRS_JSON_STRING}}", exprs_json_string)
    with open("desmos.html", "w", encoding="utf8") as dst_file:
        dst_file.write(dst_content)

