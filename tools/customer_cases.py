"""Customer-oriented presentation layer over the recorded technical case studies."""
from pathlib import Path
import re,html
R=Path(__file__).resolve().parents[1]
DATA={
'demandcast':('Zaplanuj popyt na jutro.','Plan tomorrow’s demand.','Prognoza liczby wypożyczeń na kolejne 24 godziny.','Forecast rental demand for the next 24 hours.','24 h','horyzont prognozy','forecast horizon','Średni błąd w teście: 66 wypożyczeń na godzinę.','Average test error: 66 rentals per hour.'),
'intentroute':('Przekaż zgłoszenie do właściwej kolejki.','Send requests to the right queue.','Czyta wiadomość i rozpoznaje, z czym klient potrzebuje pomocy.','Reads a message and identifies what the customer needs help with.','90.7%','poprawnych klasyfikacji w teście EN','correct classifications in the English test','77 kategorii bankowych. Polski zestaw kontrolny jest mały.','77 banking categories. The Polish control set is small.'),
'terravision':('Rozpoznaj, co widać na zdjęciu.','Recognize what an image shows.','Rozróżnia las, wodę, zabudowę i inne typy terenu na zdjęciach satelitarnych.','Identifies forest, water, buildings and other land-cover types in satellite images.','96.57%','poprawnych odpowiedzi w teście','correct answers in the test','4050 zdjęć testowych; nowe regiony wymagają osobnej oceny.','4,050 test images; new regions require separate evaluation.'),
'machinesentinel':('Zauważ nietypową pracę maszyny.','Spot unusual machine behavior.','Porównuje odczyty czujników z normalnym zakresem pracy. Prototyp badawczy.','Compares sensor readings with normal operation. Research prototype.','PROTOTYP','wymaga dalszego rozwoju','requires further development','Wykrył 29% awarii w syntetycznym teście. To za mało do samodzielnego monitoringu.','Detected 29% of failures in the synthetic test. Insufficient for standalone monitoring.'),
'basketwise':('Pokaż klientowi kolejne trafne produkty.','Show customers more relevant products.','Dobiera propozycje do historii zakupów i zawartości koszyka.','Tailors suggestions to purchase history and basket contents.','2.24×','lepszy wynik rankingu niż popularność','better ranking score than popularity','Porównanie NDCG@10. Nie oznacza wzrostu sprzedaży o 2,24×.','NDCG@10 comparison. This does not mean 2.24× higher sales.'),
'reviewpulse':('Zobacz, jak klienci oceniają doświadczenie.','See how customers feel about their experience.','Porządkuje opinie na pozytywne i negatywne, pojedynczo lub z pliku.','Organizes feedback into positive and negative sentiment, individually or in batches.','91.8%','poprawnych klasyfikacji w teście EN','correct classifications in the English test','Dwa rodzaje opinii; bez klasy neutralnej.','Two sentiment classes; no neutral class.'),
'ai-desk':('Znajdź odpowiedź w firmowych dokumentach.','Find answers in company documents.','Odpowiada na pytania i pokazuje źródło dostępne dla Twojej roli.','Answers questions and shows sources accessible to your role.','40','dokumentów w demonstracyjnej bazie','documents in the demo collection','67/70 kontroli wyszukiwania; odpowiedzi i cytowania wymagają weryfikacji.','67/70 retrieval checks; answers and citations require verification.')}
def t(pl,en,tag='span',cls=''):
 return f'<{tag} class="{cls}" data-pl="{html.escape(pl,quote=True)}" data-en="{html.escape(en,quote=True)}">{html.escape(pl)}</{tag}>'
def visual(slug):
 s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 390"><rect width="720" height="390" rx="18" fill="#181e25"/><g font-family="Arial,sans-serif" fill="#f4f2ee">'
 def txt(x,y,text,size=18,color='#f4f2ee'):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{html.escape(text)}</text>'
 def box(x,y,w,h,fill='#242e37'):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}"/>'
 if slug=='demandcast':
  s+=txt(38,48,'A DAY, PLANNED',12,'#66dece')
  for y in [110,180,250,320]:s+=f'<path d="M40 {y}H680" stroke="#34414c"/>'
  s+='<path d="M40 300L90 290L140 275L190 165L240 105L290 200L340 225L390 210L440 170L490 75L540 115L590 240L640 280L680 290" fill="none" stroke="#ff681f" stroke-width="5"/>'
  s+=box(445,27,220,44)+txt(462,55,'24 HOURS AHEAD',15)+txt(40,358,'06:00',12)+txt(330,358,'12:00',12)+txt(630,358,'18:00',12)
 elif slug=='intentroute':
  s+=box(32,120,260,140)+txt(53,159,'“Where is my card?”',21)+txt(53,199,'A customer message',14,'#aeb8bf')
  for i,label in enumerate(['Card delivery','Payments','Account access']):
   y=48+i*110;s+=box(430,y,250,74,'#304a42' if i==0 else '#242e37')+txt(450,y+43,label,19)
   s+=f'<path d="M292 190C355 190 360 {y+37} 420 {y+37}" fill="none" stroke="{"#66dece" if i==0 else "#43505b"}" stroke-width="{4 if i==0 else 1}"/>'
 elif slug=='terravision':
  colors=['#647b46','#284e3c','#326b7e','#8a8778']
  for i,name in enumerate(['CROPS','FOREST','WATER','BUILDINGS']):
   x=32+(i%2)*345;y=28+(i//2)*175;s+=box(x,y,320,152,colors[i]);
   for j in range(7):s+=f'<path d="M{x+15+j*45} {y+10}l60 130" stroke="#ffffff24" stroke-width="14"/>'
   s+=txt(x+20,y+128,name,18)
 elif slug=='machinesentinel':
  s+=txt(35,48,'SENSOR REVIEW',12,'#66dece')
  for i,(label,val,level) in enumerate([('Temperature','298.9 K',.45),('Speed','2737 rpm',.92),('Torque','8.8 Nm',.18)]):
   y=96+i*92;s+=txt(35,y,label,16)+txt(555,y,val,21)+box(35,y+18,620,12,'#303c46')+box(35,y+18,620*level,12,'#ff681f' if i else '#66dece')
  s+=txt(35,365,'RESEARCH PROTOTYPE · HUMAN REVIEW REQUIRED',12,'#ffb281')
 elif slug=='basketwise':
  s+=box(40,112,180,190,'#38504a')+txt(62,150,'YOUR BASKET',12,'#66dece')+txt(104,223,'♡',65)+txt(76,273,'Heart candle',17)
  for i,label in enumerate(['Red variant','Decorations','Gift idea']):
   x=285+i*140;y=55+(i%2)*130;s+=f'<path d="M220 205Q{x-10} 205 {x} {y+70}" stroke="#66dece" fill="none"/>'+box(x,y,120,140)+txt(x+45,y+60,['♡','✦','◇'][i],40,'#ffb281')+txt(x+10,y+115,label,13)
 elif slug=='reviewpulse':
  s+=txt(35,48,'THE VOICE OF YOUR CUSTOMERS',12,'#66dece')
  for i,(label,value,color) in enumerate([('“Great service.”','POSITIVE','#66dece'),('“Delivery was late.”','NEGATIVE','#ff9a6b'),('“I loved the product.”','POSITIVE','#66dece')]):
   y=78+i*96;s+=box(30,y,660,76)+txt(52,y+45,label,20)+txt(518,y+45,value,12,color)
 else:
  s+=box(145,35,530,72,'#34483f')+txt(167,79,'What is the learning budget?',20)+box(35,145,580,170)+txt(58,187,'2000 PLN per employee.',25)+txt(58,224,'Source: Learning budget policy',15,'#66dece')+txt(58,273,'Only documents you can access.',14,'#aeb8bf')
 return s+'</g></svg>'
def apply():
 for slug,d in DATA.items():
  p=R/(slug+'.html');s=p.read_text(encoding='utf8');(R/'case-study-assets'/f'{slug}-story.svg').write_text(visual(slug),encoding='utf8')
  s=re.sub(r'<section class="wrap section" id="model">.*?</section>','',s,flags=re.S)
  s=re.sub(r'<div class="engineering-strip">.*?</div>','',s,flags=re.S).replace('ML ENGINEERING','JAK TO DZIAŁA / HOW IT WORKS')
  s=s.replace('href="#model"','href="#example"').replace('>Model</span>','>Przykład</span>').replace('data-pl="Model" data-en="Model"','data-pl="Przykład" data-en="Example"').replace('<section class="wrap example-section">','<section class="wrap example-section" id="example">')
  s=re.sub(r'<h1>.*?</h1>',t(d[0],d[1],'h1'),s,count=1,flags=re.S)
  s=re.sub(r'<p class="case-lead".*?</p>',t(d[2],d[3],'p','case-lead'),s,count=1,flags=re.S)
  s=re.sub(r'<div class="hero-value">.*?</div>',f'<div class="hero-value">{d[4]}</div>',s,count=1)
  s=re.sub(r'<p class="metric-unit".*?</p>',t(d[5],d[6],'p','metric-unit'),s,count=1,flags=re.S)
  s=re.sub(r'<p class="metric-scope".*?</p>',t(d[7],d[8],'p','metric-scope'),s,count=1,flags=re.S)
  s=s.replace(f'{slug}-weights.svg',f'{slug}-story.svg').replace('Actual model evidence','Illustrative use scenario')
  s=s.replace('SAVED ARTIFACTS / REPRODUCIBLE RESULTS','SCENARIUSZ DZIAŁANIA / USE SCENARIO')
  s=re.sub(r'<section class="wrap section" id="results">(.*?)</section>',lambda m:'<details class="wrap customer-details" id="results"><summary>'+t('Jak zmierzyliśmy wynik?','How did we measure it?')+'<b>＋</b></summary>'+m[1]+'</details>',s,flags=re.S)
  s=s.replace('</head>','<link rel="stylesheet" href="case-study-assets/customer.css"></head>')
  s=s.replace('Zajrzyj do modelu','Zobacz przykład').replace('Inside the model','See an example').replace('Konkretny input. Czytelny output.','Tak wygląda to w praktyce.').replace('A concrete input. A clear output.','See it in practice.')
  p.write_text(s,encoding='utf8')
 p=R/'index.html';s=p.read_text(encoding='utf8')
 for slug,d in DATA.items():
  pattern=r'(<a class="case-index-card" href="'+re.escape(slug)+r'\.html">)(.*?)(</a>)'
  def card(m):
   body=m[2].replace(f'{slug}-weights.svg',f'{slug}-story.svg');body=re.sub(r'<p .*?</p>',t(d[2],d[3],'p'),body,count=1,flags=re.S)
   body=re.sub(r'<div class="index-metric">.*?</div>','<div class="index-metric"><strong>'+d[4]+'</strong>'+t(d[5],d[6])+'</div>'+t(d[7],d[8],'p','card-context')+'<span class="card-action">'+t('Poznaj projekt','Explore project')+' <b>↗</b></span>',body,flags=re.S)
   return m[1]+body+m[3]
  s=re.sub(pattern,card,s,flags=re.S)
 s=s.replace('terravision.html#model','terravision.html#example').replace('>Model</span>','>Przykład</span>').replace('data-pl="Model" data-en="Model"','data-pl="Przykład" data-en="Example"')
 s=s.replace('Poznaj ich zadania, architekturę, mierzone wyniki i możliwości zastosowania.','Zobacz, jakie problemy pomagają rozwiązać i jak działają w praktyce.').replace('Explore their purpose, architecture, measured results and application opportunities.','See which problems they help solve and how they work in practice.')
 s=s.replace('</head>','<link rel="stylesheet" href="case-study-assets/customer.css"></head>');p.write_text(s,encoding='utf8')
if __name__=='__main__':apply()
