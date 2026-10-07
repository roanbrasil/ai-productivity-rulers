"""Figures of the article, white background.   python3 figs.py pt|en   (run from the article folder)"""
import json
import os
import sys

import graphviz
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

LANG = sys.argv[1]; pt = LANG == 'pt'
BG = '#ffffff'; INK = '#20202e'; BLUE = '#3b5b92'; BLUEF = '#cddaeb'; GREEN = '#4a7c59'; GREENF = '#cbdccf'
RED = '#bf4f4a'; REDF = '#ecccc9'; AMBER = '#c98a2b'; AMBERF = '#eddcc0'; GREY = '#8d8d8d'
os.makedirs('images', exist_ok=True)
R = json.load(open('results/rulers.json'))
pct = (lambda v, d=0: f'{v * 100:+.{d}f}%'.replace('.', ',').replace('-', '−')) if pt else (lambda v, d=0: f'{v * 100:+.{d}f}%'.replace('-', '−'))
num = (lambda v: f'{v:,.0f}'.replace(',', '.')) if pt else (lambda v: f'{v:,.0f}')

mpl.rcParams.update({'figure.facecolor': BG, 'axes.facecolor': BG, 'savefig.facecolor': BG, 'font.family': 'serif', 'font.size': 13,
                     'axes.edgecolor': INK, 'axes.labelcolor': INK, 'text.color': INK, 'xtick.color': INK, 'ytick.color': INK,
                     'axes.grid': True, 'grid.color': '#dddddd', 'grid.linewidth': 0.8, 'axes.linewidth': 1.1})
pctfmt = mpl.ticker.FuncFormatter(lambda v, _: '0%' if abs(v) < 1e-9 else pct(v / 100))

# ------------------------------------------------------------ fig 1: five rulers, same 246 tasks
ss = {r['rule']: r['change'] for r in R['self_selected']}
rows = [  # (label, value, lo, hi, color)
    ('Perguntar antes\n(previsão dos devs, por tarefa)' if pt else "Ask beforehand\n(developers' forecast, per task)", R['forecast']['change_ratio_of_sums'], None, None, BLUE),
    ('Dashboard: IA nas tarefas curtas' if pt else 'Dashboard: AI on the short tasks', ss['short_tasks'], None, None, AMBER),
    ('Dashboard: IA onde o dev\nespera maior ganho' if pt else 'Dashboard: AI where the developer\nexpects the biggest gain', ss['largest_expected_gain'], None, None, AMBER),
    ('Dashboard: IA nas tarefas longas' if pt else 'Dashboard: AI on the long tasks', ss['long_tasks'], None, None, AMBER),
    ('Sorteio, sem estimativa prévia' if pt else 'Randomized, no prior estimate', R['randomized_without_estimate']['estimate'], R['randomized_without_estimate']['lo'], R['randomized_without_estimate']['hi'], GREY),
    ('Sorteio, com estimativa prévia\n(a conta da METR)' if pt else "Randomized, with prior estimate\n(METR's specification)", R['randomized_with_estimate']['estimate'], R['randomized_with_estimate']['lo'], R['randomized_with_estimate']['hi'], RED),
]
XMAX = 110
fig, ax = plt.subplots(figsize=(11.5, 5.6), layout='constrained')
for i, (lab, v, lo, hi, col) in enumerate(rows):
    x = min(v * 100, XMAX - 12)
    if lo is not None:
        ax.plot([lo * 100, hi * 100], [i, i], color=col, lw=2.4, solid_capstyle='butt', zorder=3)
        ax.plot([lo * 100] * 2, [i - .13, i + .13], color=col, lw=2.4, zorder=3); ax.plot([hi * 100] * 2, [i - .13, i + .13], color=col, lw=2.4, zorder=3)
    ax.scatter([x], [i], s=170, color=col, zorder=4, edgecolor='white', linewidth=1.2)
    clipped = v * 100 > XMAX - 12
    if clipped:
        ax.annotate('', xy=(XMAX - 2, i), xytext=(x + 2, i), arrowprops=dict(arrowstyle='->', color=col, lw=2))
    if lo is not None:
        ax.text(hi * 100 + 3, i, f"{pct(v)}   [{pct(lo)} {'a' if pt else 'to'} {pct(hi)}]", ha='left', va='center', fontsize=12.5, fontweight='bold', color=col)
    else:
        ax.text(x, i - 0.36, pct(v), ha='center', va='center', fontsize=12.5, fontweight='bold', color=col)
ax.axvline(0, color=INK, lw=1.3, zorder=2)
ax.set_yticks(range(len(rows)), [r[0] for r in rows]); ax.invert_yaxis(); ax.set_ylim(len(rows) - 0.45, -0.75)
ax.set_xlim(-62, XMAX); ax.xaxis.set_major_formatter(pctfmt); ax.grid(axis='y', visible=False)
ax.set_xlabel('mudança no tempo por tarefa atribuída à IA  (negativo = mais rápido)' if pt else 'change in time per task attributed to AI  (negative = faster)')
fig.savefig(f'images/fig1_{LANG}.png', dpi=150, bbox_inches='tight'); plt.close(fig)

# ------------------------------------------------------------ fig 3: what a pilot of n tasks concludes
P = R['pilots']; n = [p['n'] for p in P]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.9), layout='constrained')
a1.fill_between(n, [p['p10'] * 100 for p in P], [p['p90'] * 100 for p in P], color=BLUEF, zorder=2,
                label='80% dos pilotos caem nesta faixa' if pt else '80% of pilots land in this band')
a1.plot(n, [p['median'] * 100 for p in P], color=BLUE, lw=2.2, zorder=3, label='mediana' if pt else 'median')
a1.axhline(0, color=INK, lw=1.2, zorder=2)
a1.set_xlabel('tarefas no piloto' if pt else 'tasks in the pilot'); a1.yaxis.set_major_formatter(pctfmt)
a1.set_title('Estimativa do efeito da IA no tempo' if pt else "Estimated effect of AI on time", loc='left', fontsize=13, pad=10)
a1.legend(loc='upper right', frameon=False, fontsize=11); a1.set_xticks(n); a1.set_xticklabels(n, fontsize=11); a1.set_xlim(15, 251)
a2.plot(n, [p['inconclusive'] * 100 for p in P], color=RED, lw=2.4, marker='o', ms=7, zorder=3)
a2.plot(n, [p['says_ai_is_faster'] * 100 for p in P], color=AMBER, lw=2.4, marker='s', ms=7, zorder=3)
a2.text(96, 86, 'não conclui nada\n(IC de 95% inclui o zero)' if pt else 'concludes nothing\n(95% CI includes zero)', color=RED, fontsize=11.5, va='center')
a2.text(96, 20, 'aponta o sinal contrário\nao do estudo completo' if pt else 'points the opposite way\nfrom the full study', color=AMBER, fontsize=11.5, va='center')
a2.set_ylim(0, 100); a2.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(decimals=0)); a2.set_xticks(n); a2.set_xticklabels(n, fontsize=11); a2.set_xlim(15, 251)
a2.set_xlabel('tarefas no piloto' if pt else 'tasks in the pilot')
a2.set_title('Parte dos pilotos que…' if pt else 'Share of pilots that…', loc='left', fontsize=13, pad=10)
fig.text(0.01, -0.06, ('4.000 pilotos reamostrados por tamanho, com reposição, das 246 tarefas reais.' if pt else
                       '4,000 pilots resampled per size, with replacement, from the 246 real tasks.'), fontsize=10, color=GREY)
fig.savefig(f'images/fig3_{LANG}.png', dpi=150, bbox_inches='tight'); plt.close(fig)

# ------------------------------------------------------------ fig 2: one developer at a time
D = R['per_developer']['rows']
fig, ax = plt.subplots(figsize=(10.5, 6.4), layout='constrained')
for i, r in enumerate(D):
    ax.plot([1 + r['lo'], 1 + r['hi']], [i, i], color=GREY, lw=2, zorder=2)
    ax.scatter([1 + r['estimate']], [i], s=80, color=RED if r['estimate'] > 0 else GREEN, zorder=4, edgecolor='white')
    ax.scatter([1 + r['forecast']], [i], s=70, marker='D', color=BLUE, zorder=3, edgecolor='white')
ax.axvline(1, color=INK, lw=1.3)
ax.set_xscale('log'); ticks = [0.33, 0.5, 0.75, 1, 1.5, 2.5, 5, 9]
ax.set_xticks(ticks, ['0%' if t == 1 else pct(t - 1) for t in ticks]); ax.minorticks_off(); ax.set_xlim(0.26, 10.5)
ax.set_yticks(range(len(D)), [f"dev {chr(65 + i)}  ·  {r['n']} " + ('tarefas' if pt else 'tasks') for i, r in enumerate(D)], fontsize=11.5)
ax.invert_yaxis(); ax.grid(axis='y', visible=False)
ax.set_xlabel('mudança no tempo por tarefa com IA  (escala log)' if pt else 'change in time per task with AI  (log scale)')
h = [mpl.lines.Line2D([], [], marker='D', color='w', markerfacecolor=BLUE, ms=9, label='previsão do próprio dev' if pt else "the developer's own forecast"),
     mpl.lines.Line2D([], [], marker='o', color='w', markerfacecolor=RED, ms=10, label='medido: mais lento' if pt else 'measured: slower'),
     mpl.lines.Line2D([], [], marker='o', color='w', markerfacecolor=GREEN, ms=10, label='medido: mais rápido' if pt else 'measured: faster'),
     mpl.lines.Line2D([], [], color=GREY, lw=2, label='IC de 95%' if pt else '95% CI')]
ax.legend(handles=h, loc='upper center', bbox_to_anchor=(0.5, -0.13), ncol=4, frameon=False, fontsize=11)
fig.savefig(f'images/fig2_{LANG}.png', dpi=150, bbox_inches='tight'); plt.close(fig)

# ------------------------------------------------------------ fig 4: the measurement design
T = dict(
    out=('1  RESULTADO\nque a empresa já media antes da IA\ne que acontece milhares de vezes' if pt else '1  OUTCOME\nthe company already measured before AI\nand that happens thousands of times'),
    est=('2  ESTIMATIVA PRÉVIA\nquanto esta unidade de trabalho\ndeveria levar, anotado antes' if pt else '2  PRIOR ESTIMATE\nhow long this unit of work\nshould take, written down first'),
    q=('A IA já é o\njeito padrão\nde trabalhar?' if pt else 'Is AI already\nthe default way\nof working?'),
    task=('3a  SORTEIO POR TAREFA\ncara ou coroa: com IA / sem IA' if pt else '3a  RANDOMIZE BY TASK\ncoin flip: AI / no AI'),
    team=('3b  ROLLOUT ESCALONADO\nsorteia a ORDEM em que\nas equipes recebem a ferramenta' if pt else '3b  STAGGERED ROLLOUT\nrandomize the ORDER in which\nteams get the tool'),
    eff=('4  EFEITO COM INTERVALO\nregressão do resultado no sorteio\n+ estimativa prévia' if pt else '4  EFFECT WITH AN INTERVAL\nregress the outcome on the coin flip\n+ the prior estimate'),
    guard=('5  O QUE ENTRA NA CONTA\nretrabalho e revisão no tempo\nqualidade como guard-rail\ncusto por tarefa concluída' if pt else '5  WHAT GOES ON THE BILL\nrework and review in the time\nquality as a guardrail\ncost per completed task'),
    use=('Tokens, licenças ativas, pesquisa\nDIAGNÓSTICO, nunca meta' if pt else 'Tokens, active seats, surveys\nDIAGNOSTIC, never a target'),
    no='não' if pt else 'no', yes='sim' if pt else 'yes')
g = graphviz.Digraph(format='png')
g.attr(rankdir='TB', bgcolor=BG, nodesep='0.55', ranksep='0.42', fontname='Georgia', dpi='150', newrank='true')
g.attr('node', shape='box', style='rounded,filled', fontname='Georgia', fontsize='13', color=INK, penwidth='1.4', margin='0.2,0.13', fillcolor='#f1efe8')
g.attr('edge', color=INK, penwidth='1.4', fontname='Georgia', fontsize='12', arrowsize='0.8')
g.node('out', T['out'], fillcolor=GREENF, color=GREEN); g.node('est', T['est'], fillcolor=GREENF, color=GREEN)
g.node('q', T['q'], shape='diamond', fillcolor=AMBERF, color=AMBER, margin='0.05,0.05')
g.node('task', T['task'], fillcolor=BLUEF, color=BLUE); g.node('team', T['team'], fillcolor=BLUEF, color=BLUE)
g.node('eff', T['eff'], fillcolor=REDF, color=RED); g.node('guard', T['guard'])
g.node('use', T['use'], style='rounded,dashed,filled', color=GREY, fontcolor=GREY, fillcolor=BG)
g.edge('out', 'est'); g.edge('est', 'q'); g.edge('q', 'task', label=T['no']); g.edge('q', 'team', label=T['yes'])
g.edge('task', 'eff'); g.edge('team', 'eff'); g.edge('eff', 'guard'); g.edge('guard', 'use', style='dashed', color=GREY, arrowhead='none')
g.render(f'images/fig4_{LANG}', cleanup=True)
print('ok', LANG)
