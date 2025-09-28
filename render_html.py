from __future__ import annotations
import html, re
from typing import Dict, List, Mapping, Iterable, Tuple

# ColorBrewer Set3 palette (Bokeh Set3[12])
SET3_12 = [
    "#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072", "#80B1D3", "#FDB462",
    "#B3DE69", "#FCCDE5", "#D9D9D9", "#BC80BD", "#CCEBC5", "#FFED6F"
]

def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s)
    return s[:64].strip("-") or "section"

def _stable_index(name: str, n: int) -> int:
    # FNV-1a 32-bit
    h = 2166136261
    for ch in name.lower().encode("utf-8"):
        h ^= ch
        h = (h * 16777619) & 0xffffffff
    return h % n

def _area_color(area: str) -> str:
    return SET3_12[_stable_index(area, len(SET3_12))]

def _iter_items(items: Iterable) -> Iterable[Tuple[str, str]]:
    """Yield (desc, url) from a list like [{desc:url}, ...]"""
    for it in items:
        if isinstance(it, Mapping):
            for k, v in it.items():
                yield str(k), str(v)
                break
        else:
            try:
                desc, url = it
                yield str(desc), str(url)
            except Exception:
                continue

HTML_SHELL = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>%%TITLE%%</title>
  <style>
    :root{
      --fg:#121826; --muted:#5b677a; --bg:#ffffff;
      --card:#ffffff; --link:#175cd3;
    }
    html,body{
      margin:0; padding:0; background:var(--bg); color:var(--fg);
      font:13px/1.34 system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,"Apple Color Emoji","Segoe UI Emoji";
    }
    /* Top nav pills (Set3 per area) */
    .topnav{
      position:sticky; top:0; background:rgba(255,255,255,.98);
      backdrop-filter:saturate(140%) blur(6px);
      border-bottom:1px solid #eaeef7; z-index:10;
    }
    .topnav-inner{
      max-width:1200px; margin:0 auto; padding:6px 12px; display:flex; gap:6px; flex-wrap:wrap;
    }
    .pill{
      --area-color:#8DD3C7;
      text-decoration:none; padding:5px 9px; border-radius:999px;
      color:#0d1b2a;
      background: color-mix(in oklab, var(--area-color) 35%, white);
      border:1px solid color-mix(in oklab, var(--area-color) 55%, white);
    }
    .pill:hover,.pill:focus{
      outline:none;
      border-color: color-mix(in oklab, var(--area-color) 70%, white);
      background: color-mix(in oklab, var(--area-color) 50%, white);
      color:#0a1a3a;
    }

    main{ max-width:1200px; margin:18px auto; padding:0 12px; }

    /* Horizontal bands — one per Area */
    .band{
      --area-color:#8DD3C7;
      background: color-mix(in oklab, var(--area-color) 18%, white);
      border-top:1px solid color-mix(in oklab, var(--area-color) 55%, white);
      border-bottom:1px solid color-mix(in oklab, var(--area-color) 55%, white);
      padding:10px 10px 12px;
      margin:10px 0;
    }
    .band-header{
      font-weight:700; font-size:13px; margin:0 0 6px 2px; color:#0a1a3a; letter-spacing:.2px;
    }
    /* Subareas inside band, arranged in columns */
    .band-grid{
      display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:0;
      border-left:1px solid color-mix(in oklab, var(--area-color) 45%, white);
      background: transparent;
    }
    .subcol{
      padding:8px 10px 10px;
      border-right:1px solid color-mix(in oklab, var(--area-color) 45%, white);
    }
    .subcol + .subcol{
      box-shadow: -0.5px 0 0 0 color-mix(in oklab, var(--area-color) 60%, white) inset;
    }
    .subcard{
      background: var(--card);
      border:1px solid color-mix(in oklab, var(--area-color) 35%, white);
      border-radius:10px;
      padding:8px 10px;
    }
    h2{
      font-size:13px; margin:0 0 4px; font-weight:650; color:#0a1a3a;
      white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    }
    ol.linklist{ margin:0; padding-left:16px; }
    ol.linklist li{ margin:0; line-height:1.25; }
    ol.linklist li + li{ margin-top:2px; }
    a.link{ color: #0f4ac6; text-decoration:none; }
    a.link:hover, a.link:focus{ text-decoration:underline; color: #0c3aa0; outline:none; }

    @media (max-width: 520px){
      .band-grid{ grid-template-columns: 1fr; }
      .subcol{ border-right:none; box-shadow:none; border-bottom:1px solid color-mix(in oklab, var(--area-color) 45%, white); }
      .subcol:last-child{ border-bottom:none; }
    }
  </style>
</head>
<body>
  <nav class="topnav" aria-label="Areas">
    <div class="topnav-inner">
%%NAV%%
    </div>
  </nav>
  <main>
%%BANDS%%
  </main>
</body>
</html>"""

def render_html(pages: Dict[str, Dict[str, List[Mapping[str, str]]]], title: str = "Links") -> str:
    nav_parts = []
    bands = []

    # Top menu
    for area in sorted(pages.keys(), key=str.lower):
        area_id = _slug(area)
        color = _area_color(area)
        nav_parts.append(
            '      <a class="pill" href="#{id}" style="--area-color:{color}">{label}</a>'.format(
                id=html.escape(area_id),
                color=html.escape(color),
                label=html.escape(area),
            )
        )

    # Bands (each area one horizontal band)
    for area in sorted(pages.keys(), key=str.lower):
        area_id = _slug(area)
        color = _area_color(area)
        submap = pages.get(area) or {}

        subcols = []
        if submap:
            for sub in sorted(submap.keys(), key=str.lower):
                lines = []
                for desc, url in _iter_items(submap.get(sub) or []):
                    lines.append('            <li><a class="link" href="{url}" target="_blank" rel="noopener">{desc}</a></li>'.format(
                        url=html.escape(url, quote=True),
                        desc=html.escape(desc),
                    ))
                links_html = "\n".join(lines)
                heading = "{area} - {sub}".format(area=area, sub=sub)
                subcols.append(
                    "      <div class=\"subcol\">\n"
                    "        <div class=\"subcard\">\n"
                    "          <h2>{heading}</h2>\n"
                    "          <ol class=\"linklist\">\n"
                    "{links}\n"
                    "          </ol>\n"
                    "        </div>\n"
                    "      </div>".format(heading=html.escape(heading), links=links_html)
                )
        else:
            subcols.append(
                "      <div class=\"subcol\"><div class=\"subcard\"><h2>{}</h2><ol class=\"linklist\"></ol></div></div>".format(
                    html.escape(area + " - (no subareas)")
                )
            )

        bands.append(
            "    <section class=\"band\" id=\"{id}\" style=\"--area-color:{color}\">\n"
            "      <div class=\"band-header\">{label}</div>\n"
            "      <div class=\"band-grid\">\n"
            "{subcols}\n"
            "      </div>\n"
            "    </section>".format(
                id=html.escape(area_id), color=html.escape(color), label=html.escape(area), subcols="\n".join(subcols)
            )
        )

    html_page = HTML_SHELL.replace("%%TITLE%%", html.escape(title))
    html_page = html_page.replace("%%NAV%%", "\n".join(nav_parts))
    html_page = html_page.replace("%%BANDS%%", "\n".join(bands))
    return html_page

if __name__ == "__main__":
    demo_pages = {
        "Developments": {
            "E2E examples": [
                {"The first eVTOL air taxi that actually looks safe": "https://example.com/evtol-safe"}
            ],
            "Prototypes": [
                {"Quad-copter ESC tuning checklist": "https://example.com/esc-tuning"}
            ]
        },
        "AI": {
            "E2E examples": [
                {"localstack SageMaker deployment with model": "https://example.com/localstack-sagemaker"}
            ],
            "Papers": [
                {"Causal Inference for Recommenders": "https://example.com/causal-rec"}
            ]
        },
        "AWS": {
            "Papers": [
                {"Hugging Face and AWS partner to make AI more accessible": "https://aws.amazon.com/blogs/machine-learning/"},
                {"Cookbook for ingesting and classifying video on SageMaker": "https://example.com/cookbook"}
            ]
        },
        "Documents indexers and query": {}
    }
    open("index.set3.bands.demo.html","w",encoding="utf-8").write(render_html(demo_pages,"Set3 Bands Demo"))
    print("Wrote index.set3.bands.demo.html")
