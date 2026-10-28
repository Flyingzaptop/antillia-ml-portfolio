"""Generate readable, bilingual report artifacts from measured project outputs."""
from pathlib import Path
import json,html,csv
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
FONT=Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('ArialLocal',str(FONT/'arial.ttf')))
pdfmetrics.registerFont(TTFont('ArialLocalBold',str(FONT/'arialbd.ttf')))
pdfmetrics.registerFontFamily('ArialLocal',normal='ArialLocal',bold='ArialLocalBold',italic='ArialLocal',boldItalic='ArialLocalBold')
styles=getSampleStyleSheet()
for s in styles.byName.values():s.fontName='ArialLocal';s.leading=16
styles.add(ParagraphStyle(name='ReportTitle',fontName='ArialLocalBold',fontSize=28,leading=34,textColor=colors.HexColor('#203d45'),spaceAfter=12))
styles.add(ParagraphStyle(name='Kicker',fontName='ArialLocalBold',fontSize=8,leading=12,textColor=colors.HexColor('#9a7554'),spaceAfter=14))
styles['Heading2'].fontName='ArialLocalBold';styles['Heading2'].fontSize=15;styles['Heading2'].leading=21
styles['BodyText'].fontSize=9.5;styles['BodyText'].leading=15;styles['BodyText'].spaceAfter=9
styles['Normal'].fontSize=9;styles['Normal'].leading=14
specs=[
('01-demandcast','DemandCast','Prognozowanie popytu / Demand forecasting','UCI Bike Sharing, CC BY 4.0','https://doi.org/10.24432/C5W894','168 godzin historii i znany kalendarz. Podział czasowy 70/15/15; horyzont 24 h. Przyszła pogoda wykluczona. / 168 historical hours and known calendar. Chronological 70/15/15 split; 24-hour horizon; no future weather.','Baseline sezonowy wygrał na walidacji. GRU była trenowana, ale uzyskała gorsze wyniki. Dane historyczne jednego miasta nie potwierdzają uogólnienia. / Seasonal baseline won validation. The trained GRU performed worse. One historical city does not establish generalization.'),
('02-intentroute','IntentRoute','Klasyfikacja intencji / Intent classification','BANKING77, CC BY 4.0','https://huggingface.co/datasets/PolyAI/banking77','Oficjalny test po deduplikacji; validation wydzielone z train. TF-IDF porównany z wielojęzycznymi embeddings i MLP. / Deduplicated official test; validation from training. TF-IDF compared with multilingual embeddings and MLP.','Polska próba jest mała i autorska, nie jest niezależnym benchmarkiem. Wynik dotyczy 77 bankowych intencji. / Polish controls are small and author-written, not an independent benchmark. Results concern 77 banking intents.'),
('03-terravision','TerraVision','Pokrycie terenu / Land-cover classification','EuroSAT RGB, MIT','https://zenodo.org/records/7711810','ResNet18 z transfer learning, porównanie z cechami obrazów. Train/validation/test rozdzielone, brak identycznych hashy. / Transfer-learned ResNet18 compared with image features; disjoint train/validation/test without identical hashes.','Podział obrazów nie dowodzi przenoszenia na nowy region. Grad-CAM jest wizualizacją, nie dowodem przyczynowym. / Image-level splits do not prove transfer to a new region. Grad-CAM is a visualization, not causal evidence.'),
('04-machinesentinel','MachineSentinel','Anomalie maszyn / Machine anomalies','AI4I 2020, CC BY 4.0','https://doi.org/10.24432/C5HS5C','Autoencoder i Isolation Forest; trening wyłącznie na normalnych obserwacjach. Model oraz próg wybrane na validation. / Autoencoder and Isolation Forest trained only on normal observations. Model and threshold selected on validation.','AI4I jest syntetyczne. Niska pełność wybranego progu ogranicza przydatność; projekt nie jest gotowym systemem ochrony maszyn. / AI4I is synthetic. Limited threshold recall constrains utility; this is not a deployed equipment safety system.'),
('05-basketwise','BasketWise','Rekomendacje produktów / Product recommendations','UCI Online Retail, CC BY 4.0','https://doi.org/10.24432/C5BW33','Chronologiczny podział dni 70/15/15. Katalog tylko z train. Pełny ranking 1600 produktów; popularity, item-item i SVD. / Chronological day split 70/15/15. Train-only catalog. Full ranking of 1600 products; popularity, item-item and SVD.','Ocena ograniczona do znanych produktów nowych dla użytkownika; osobne wyniki cold start. Nie zmierzono wzrostu konwersji. / Evaluation covers known-catalog, new-to-user items, with separate cold start. Conversion uplift was not measured.'),
('06-reviewpulse','ReviewPulse','Analiza tonu / Sentiment analysis','UCI Sentiment Labelled Sentences, CC BY 4.0','https://doi.org/10.24432/C57604','Deduplikacja i stratyfikowany podział; TF-IDF oraz wielojęzyczny MLP. Wyniki domen i polskiej kontroli oddzielone. / Deduplication and stratified split; TF-IDF and multilingual MLP. Domain results and Polish controls separate.','Źródło ma wyraźnie pozytywne/negatywne zdania, bez neutralnych. Sarkazm, mieszane opinie i inne domeny mogą działać gorzej. / Source contains clearly positive/negative sentences, no neutral class. Sarcasm, mixed opinions and new domains may perform worse.')]
def metric_rows(slug,m):
    if slug.startswith(('01','05')):return [(part,name,{k:v for k,v in vals.items() if isinstance(v,(float,int))}) for part in ['validation','test'] for name,vals in m[part].items()]
    if slug.startswith(('02','06')):return [(part,name,vals[part]) for part in ['validation','test'] for name,vals in m['models'].items()]
    return [('test',name,{k:v for k,v in vals.items() if isinstance(v,(float,int)) and k!='threshold'}) for name,vals in m['models'].items()]
def number(v):return str(v) if isinstance(v,int) else f'{v:.5f}'
def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#d9e0dc'));canvas.line(46,42,549,42)
    canvas.setFont('ArialLocal',8);canvas.setFillColor(colors.HexColor('#84908a'));canvas.drawString(46,28,'ANTILLIA / REPRODUCIBLE MACHINE LEARNING');canvas.drawRightString(549,28,str(doc.page))
for slug,title,subtitle,source,url,protocol,limits in specs:
    p=ROOT/slug;report=p/'reports';report.mkdir(exist_ok=True)
    mp=next(x for x in [p/'artifacts/metrics.json',report/'metrics.json'] if x.exists());m=json.loads(mp.read_text(encoding='utf8'));rows=metric_rows(slug,m)
    selected=m.get('selected_model',m.get('config',{}).get('selected','resnet18'))
    flat=[{'split':part,'model':name,'metric':k,'value':v} for part,name,vals in rows for k,v in vals.items()]
    with (report/'results-flat.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=['split','model','metric','value']);w.writeheader();w.writerows(flat)
    metric={'01':'MAE','02':'macro_f1','03':'macro_f1','04':'pr_auc','05':'NDCG@10','06':'macro_f1'}[slug[:2]]
    test=[(name,vals[metric]) for part,name,vals in rows if part=='test' and metric in vals]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    fig,ax=plt.subplots(figsize=(8.3,3.1),layout='constrained');fig.patch.set_facecolor('#fbfcfa');ax.set_facecolor('#fbfcfa')
    bars=ax.barh([x[0] for x in test],[x[1] for x in test],color=['#d18259' if x[0]==selected else '#71958b' for x in test],height=.48)
    for bar,(_,v) in zip(bars,test):ax.text(v+max(x[1] for x in test)*.025,bar.get_y()+bar.get_height()/2,f'{v:.4f}',va='center',fontsize=10)
    ax.set_xlim(0,max(x[1] for x in test)*1.3);ax.set_xlabel(metric+(' (lower is better)' if metric=='MAE' else ' (higher is better)'));ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);fig.savefig(report/'benchmark-summary.png',dpi=160);plt.close(fig)
    story=[Paragraph('ANTILLIA / RESEARCH SERIES '+slug[:2],styles['Kicker']),Paragraph(title,styles['ReportTitle']),Paragraph(subtitle,styles['Heading2']),Paragraph('Raport eksperymentu / Experiment report',styles['BodyText']),Spacer(1,18),Paragraph('Źródło / Source',styles['Heading2']),Paragraph(html.escape(source)+'<br/>'+html.escape(url),styles['BodyText']),Paragraph('Protokół / Protocol',styles['Heading2']),Paragraph(html.escape(protocol),styles['BodyText']),Paragraph('Wybrany model / Selected model: <b>'+html.escape(selected)+'</b>',styles['BodyText']),Image(str(report/'benchmark-summary.png'),width=490,height=183),Paragraph('Wartości pochodzą z zapisanych wyników eksperymentu, nie z deklaracji producenta. / Values come from recorded experiments, not vendor claims.',styles['BodyText']),PageBreak(),Paragraph('Wyniki / Results',styles['ReportTitle'])]
    table=[['Split','Model','Metric','Value']]+[[a,b,k,number(v)] for a,b,vals in rows for k,v in vals.items() if k!='users']
    table=[[Paragraph(html.escape(str(c)),styles['Normal']) for c in r] for r in table]
    grid=Table(table,colWidths=[80,145,160,105],repeatRows=1,hAlign='LEFT');grid.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4ece5')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#dce3dc'))]));story.extend([grid,Spacer(1,18),Paragraph('Ograniczenia / Limitations',styles['Heading2']),Paragraph(html.escape(limits),styles['BodyText'])])
    if 'polish_control' in m:
        pol=m['polish_control'];story.extend([Paragraph('Polska kontrola / Polish diagnostic',styles['Heading2']),Paragraph(f"n = {pol['n']}. "+html.escape(pol['description']),styles['BodyText'])]);story.append(Paragraph(html.escape(json.dumps(pol['models'].get(selected,{}),ensure_ascii=False)),styles['BodyText']))
    if 'test_cold' in m:
        story.append(KeepTogether([Paragraph('Cold start / Nowy użytkownik',styles['Heading2']),Paragraph('Recall@10: '+f"{m['test_cold']['Recall@10']:.4f}"+' | NDCG@10: '+f"{m['test_cold']['NDCG@10']:.4f}"+' | n = '+str(m['test_cold']['users']),styles['BodyText'])]))
    story.extend([PageBreak(),Paragraph('Reprodukcja / Reproduction',styles['ReportTitle']),Paragraph('1. setup.ps1<br/>2. evaluate.ps1<br/>3. Sprawdź reports/ i zapisane tolerancje. / Inspect reports/ and recorded tolerances.',styles['BodyText']),Paragraph('Pełne konfiguracje, manifesty podziałów, pochodzenie danych, wersje bibliotek i sumy kontrolne znajdują się w projekcie. Obliczenia inference używają zapisanych wag. / Full configuration, split manifests, provenance, library versions and checksums are included in the project. Inference uses saved weights.',styles['BodyText']),Paragraph('Weryfikacja / Verification',styles['Heading2'])])
    verification=[]
    for name in ['reproduction.json','reproducibility.json']:
        if (report/name).exists():verification.append((name,json.loads((report/name).read_text(encoding='utf8'))))
    for name,v in verification:story.append(Paragraph(html.escape(name+': '+json.dumps(v,ensure_ascii=False)),styles['BodyText']))
    story.append(Paragraph('Ten raport dokumentuje własny eksperyment, nie stanowi zewnętrznego certyfikatu. / This report documents a local experiment and is not an external certification.',styles['BodyText']))
    SimpleDocTemplate(str(report/'experiment-report.pdf'),pagesize=(595,842),rightMargin=46,leftMargin=46,topMargin=46,bottomMargin=60,title=title+' Experiment Report',author='Antillia').build(story,onFirstPage=footer,onLaterPages=footer)
    if slug.startswith(('01','05')):
        card=f'# {title} — Model card PL / EN\n\n## Cel / Purpose\n{subtitle}\n\n## Dane / Data\n{source}\n{url}\n\n## Protokół / Protocol\n{protocol}\n\n## Model\nSelected on validation: {selected}\n\n## Ograniczenia / Limitations\n{limits}\n\n## Wyniki / Results\nMeasured results: reports/results-flat.csv and reports/experiment-report.pdf. Reproduce with evaluate.ps1. Training provenance and split manifests are in artifacts/.\n'
        (p/'MODEL_CARD.md').write_text(card,encoding='utf8')
        html_rows=''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in [a,b,k,number(v)])+'</tr>' for a,b,vals in rows for k,v in vals.items())
        (report/'report.html').write_text('<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+title+' report</title><style>body{font:16px/1.7 Segoe UI,sans-serif;max-width:1000px;margin:50px auto;padding:25px;color:#25433f;background:#f7f8f3}h1{font:48px Georgia}td,th{padding:12px;border-bottom:1px solid #d8dfd5;text-align:left}table{border-collapse:collapse;width:100%}img{max-width:100%}p{max-width:850px}.table{overflow:auto}</style><h1>'+title+'</h1><h2>'+subtitle+'</h2><p>'+html.escape(protocol)+'</p><img src="benchmark-summary.png" alt="Measured benchmark comparison"><div class="table"><table><tr><th>Split</th><th>Model</th><th>Metric</th><th>Value</th></tr>'+html_rows+'</table></div><h2>Limitations / Ograniczenia</h2><p>'+html.escape(limits)+'</p><a href="'+url+'">'+source+'</a><p>Reproduce: evaluate.ps1</p></html>',encoding='utf8')
    print(slug,'PDF generated')
