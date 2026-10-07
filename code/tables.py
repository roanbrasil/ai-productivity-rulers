"""Render the article tables as white-background PNGs (Medium has no tables).   python3 tables.py pt|en"""
import json
import sys

from playwright.sync_api import sync_playwright

LANG = sys.argv[1]; pt = LANG == 'pt'
R = json.load(open('results/rulers.json'))
num = (lambda v: f'{v:,.0f}'.replace(',', '.')) if pt else (lambda v: f'{v:,.0f}')
CSS = """body{margin:0;background:#fff;font-family:Georgia,serif;color:#20202e}
table{border-collapse:collapse;margin:28px;font-size:19px}
th{background:#20202e;color:#fff;text-align:left;padding:11px 16px;font-family:Arial,sans-serif;font-size:16px;white-space:nowrap}
td{padding:11px 16px;border-bottom:1px solid #dddddd;vertical-align:top}
td.n{text-align:right;white-space:nowrap} td.k{white-space:nowrap}
tr.hl td{background:#f8ebe9} tr.sep td{border-top:2px solid #20202e}
small{color:#8d8d8d;font-size:15px}"""

if pt:
    t1 = [["Quem mediu", "Amostra", "Régua", "O que saiu"],
          ["Yotzov e coautores, NBER<br><small>fev. 2026</small>", "quase 6.000 executivos, 4 países", "pesquisa", "69% das empresas usam IA; 89% não veem impacto na produtividade em 3 anos"],
          ["Baslandze e coautores, NBER<br><small>mar. 2026</small>", "cerca de 750 executivos financeiros", "pesquisa, com duas perguntas cruzadas", "ganho declarado de 1,8% em 2025; 0,6% implícito nos efeitos informados em receita e emprego"],
          ["EY-Parthenon CEO Outlook<br><small>out. 2026</small>", "1.200 CEOs, 21 países", "pesquisa", "50% apontam a IA como maior fonte de ganho; 16% enxergam o ROI em tempo real"],
          ["Faros AI<br><small>2º tri. 2026</small>", "22.000 devs, 4.000 equipes", "telemetria, antes e depois", "tarefas +33,7%; tempo de revisão 5 vezes maior; incidentes por PR 3 vezes"],
          ["METR<br><small>jul. 2025</small>", "16 devs, 246 tarefas", "sorteio por tarefa", "tempo por tarefa +19%, contra previsão de −24%"],
          ["METR<br><small>fev. 2026</small>", "57 devs, mais de 800 tarefas", "sorteio por tarefa", "−18% e −4%, com intervalos que incluem o zero; a própria METR descarta por viés de seleção"],
          ["Brynjolfsson, Li e Raymond<br><small>2023–2025</small>", "5.172 atendentes", "rollout escalonado, sem sorteio", "chamados resolvidos por hora +15%"],
          ["Cui e coautores<br><small>2024–2025</small>", "4.867 devs, 3 empresas", "sorteio de acesso", "tarefas concluídas +26%, erro-padrão de 10,3 pontos"]]
    hdr2 = ["Efeito que você quer enxergar", "Tarefas por braço,<br>com estimativa prévia", "Tarefas por braço,<br>sem estimativa prévia", "Total com estimativa", "Horas de trabalho medido"]
else:
    t1 = [["Who measured", "Sample", "Ruler", "What came out"],
          ["Yotzov and coauthors, NBER<br><small>Feb 2026</small>", "nearly 6,000 executives, 4 countries", "survey", "69% of firms use AI; 89% see no productivity impact over 3 years"],
          ["Baslandze and coauthors, NBER<br><small>Mar 2026</small>", "about 750 financial executives", "survey, two answers cross-checked", "stated gain of 1.8% in 2025; 0.6% implied by reported effects on revenue and headcount"],
          ["EY-Parthenon CEO Outlook<br><small>Oct 2026</small>", "1,200 CEOs, 21 countries", "survey", "50% name AI the biggest source of gains; 16% see ROI in real time"],
          ["Faros AI<br><small>Q2 2026</small>", "22,000 developers, 4,000 teams", "telemetry, before and after", "tasks +33.7%; review time 5x; incidents per PR 3x"],
          ["METR<br><small>Jul 2025</small>", "16 developers, 246 tasks", "randomized by task", "time per task +19%, against a forecast of −24%"],
          ["METR<br><small>Feb 2026</small>", "57 developers, 800+ tasks", "randomized by task", "−18% and −4%, intervals include zero; METR itself discounts it for selection bias"],
          ["Brynjolfsson, Li and Raymond<br><small>2023–2025</small>", "5,172 support agents", "staggered rollout, not randomized", "issues resolved per hour +15%"],
          ["Cui and coauthors<br><small>2024–2025</small>", "4,867 developers, 3 companies", "randomized access", "completed tasks +26%, standard error of 10.3 points"]]
    hdr2 = ["Effect you want to see", "Tasks per arm,<br>with prior estimate", "Tasks per arm,<br>without prior estimate", "Total with estimate", "Hours of measured work"]

hours_per_task = R['hours']['mean_task_minutes'] / 60
t2 = [hdr2]
for k, v in R['tasks_needed_per_arm'].items():
    total = 2 * v['with_estimate']
    t2.append([k, num(v['with_estimate']), num(v['without_estimate']), num(total), num(round(total * hours_per_task, -1))])


def html(rows, numeric_from=None, hl=(), sep=None, widths=None):
    out = "<table><tr>" + "".join(f"<th>{h}</th>" for h in rows[0]) + "</tr>"
    for i, r in enumerate(rows[1:]):
        cls = " ".join(c for c in ("hl" if i in hl else "", "sep" if sep == i else "") if c)
        out += f'<tr class="{cls}">' + "".join(
            f'<td class="n">{c}</td>' if numeric_from is not None and j >= numeric_from else
            f'<td style="max-width:{widths[j]}px">{c}</td>' if widths else f'<td class="k">{c}</td>'
            for j, c in enumerate(r)) + "</tr>"
    return (f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>"
            f"<div id='wrap' style='display:inline-block;background:#fff'>{out}</table></div></body></html>")


with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(device_scale_factor=2)
    for name, doc in (("tab1", html(t1, widths=[330, 250, 230, 430], sep=4)), ("tab2", html(t2, numeric_from=1, hl=(1,)))):
        pg.set_content(doc); pg.locator("#wrap").screenshot(path=f"images/{name}_{LANG}.png")
    b.close()
print("ok", LANG)
