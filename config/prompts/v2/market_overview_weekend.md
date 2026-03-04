Erstelle ein Wochenend-Briefing fuer Montagmorgen. Der Fokus liegt auf den NACHRICHTEN seit Freitagabend und dem AUSBLICK auf die kommende Woche — NICHT auf der Erklaerung vergangener Kursbewegungen.

{% if news %}
## PRIMAER-INPUT: Nachrichten seit Freitagabend

Dies sind die wichtigsten Entwicklungen seit Boersenschluss am Freitag. Diese Nachrichten sind der HAUPTINHALT deiner Analyse.

{% for item in news %}
- [{{ item.source }}] {{ item.title }}{% if item.summary %} -- {{ item.summary[:150] }}{% endif %}
{% endfor %}
{% endif %}

## REFERENZ: Freitagsschlusskurse (nur zur Einordnung)

WICHTIG: Diese Kurse stammen vom Freitagsschluss, also VOR den obigen Wochenend-Nachrichten.
Erklaere die Freitagskurse NICHT mit Wochenend-News. Die Kurse dienen nur als Ausgangspunkt
fuer die Einschaetzung, wie die Maerkte am Montag reagieren koennten.

{% for stock in indices %}
- {{ stock.name }} ({{ stock.ticker }}): {{ stock.price }} ({{ "%+.2f"|format(stock.change_pct) }}%)
{% endfor %}

{% if macro %}
Makro-Referenz: {% for ind in macro %}{{ ind.name }}: {{ ind.value }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

{% if commodities %}
Rohstoffe: {% for stock in commodities %}{{ stock.name }}: {{ stock.price }} ({{ "%+.2f"|format(stock.change_pct) }}%){% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

{% if forex %}
Devisen: {% for stock in forex %}{{ stock.name }}: {{ stock.price }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## Aufgabe: Wochenend-Briefing (Montagmorgen)

Erstelle ein vorwaertsgerichtetes Briefing das den Leser auf den Montagshandel und die Woche vorbereitet.

ZENTRALE REGEL: Die Freitagskurse sind VERGANGENHEIT. Erklaere sie NICHT ausfuehrlich.
Die Wochenend-News sind die ZUKUNFT fuer den Montagshandel. Analysiere sie ausfuehrlich.

Anforderungen pro Abschnitt:

1. **summary**: 3-4 Saetze ueber die wichtigsten WOCHENEND-ENTWICKLUNGEN.
   Was koennte den Montagshandel beeinflussen? Was sollte der Leser heute Morgen wissen?
   NICHT: "Die Maerkte schlossen am Freitag bei..." — das ist Vergangenheit.

2. **us_markets**: KURZ (2-3 Saetze). Nur: Wo standen die US-Maerkte am Freitag (1 Satz Referenz),
   dann: Wie koennten die Wochenend-News die US-Maerkte am Montag beeinflussen?
   Beispiel: "S&P 500 schloss bei 5.800 (-0.4%). Die Iran-Eskalation am Wochenende duerfte
   am Montag zu Gap-Down fuehren, besonders bei Airlines und Energieverbrauchern."

3. **european_markets**: KURZ (2-3 Saetze). Freitags-Stand + erwartete Montags-Reaktion.
   Europa-spezifische Wochenend-Entwicklungen (EZB, Politik, etc.)

4. **asian_markets**: KURZ (2-3 Saetze). Freitags-Stand + Montags-Erwartung.
   Asien handelt vor Europa/USA — was signalisieren die asiatischen Maerkte?

5. **commodities_forex**: KURZ (2-3 Saetze). Freitags-Stand + erwartete Wochenend-Gaps.
   Oel, Gold, Dollar: Wie reagieren sie auf die Wochenend-News?

6. **macro_context**: <<<HAUPTABSCHNITT - AUSFUEHRLICH SCHREIBEN>>>
   Dies ist der wichtigste Teil des Weekend-Briefings. Hier gehoert:
   - Analyse der Wochenend-News: Was bedeuten sie fuer die Maerkte?
   - Makro-Einordnung: Wie beeinflussen die News das grosse Bild (Inflation, Zinsen, Wachstum)?
   - Zentralbank-Kontext: Aendern die News etwas an den Fed/EZB-Erwartungen?
   Beispiel: "Die Iran-Eskalation koennte ueber steigende Oelpreise die Inflation wieder anheizen.
   Falls Brent ueber 90$ steigt, duerfte die Fed ihre Zinssenkungsplaene weiter verschieben.
   Aktuell preist der Markt die erste Senkung fuer September ein — das koennte sich aendern."

7. **geopolitical_context**: Wochenend-Geopolitik im Detail (falls relevant).
   Konflikte, Handelspolitik, Sanktionen, Gipfeltreffen.
   Leer lassen wenn am Wochenende nichts Geopolitisches passiert ist.

8. **forward_outlook**: <<<HAUPTABSCHNITT - AUSFUEHRLICH SCHREIBEN>>>
   Detaillierte Wochenvorschau. Fuer jeden relevanten Tag:
   - Wirtschaftsdaten (CPI, PMI, Jobs, etc.) — wann, was erwartet, warum wichtig
   - Earnings: Welche Unternehmen berichten (besonders Big Tech, Banken)
   - Zentralbank-Reden oder Sitzungen
   - Politische Termine
   Beispiel: "Dienstag: US CPI (erwartet 3.2%, vorher 3.0%) — entscheidend fuer Fed-Zinspfad.
   Mittwoch: Fed Minutes. Donnerstag: Earnings von Microsoft, Meta, Amazon."

9. **key_events**: 3-5 wichtigste Wochenend-Events MIT erwartetem Impact auf den Montagshandel.
   NICHT Freitagsereignisse, sondern Dinge die NACH Boersenschluss passiert sind.

10. **risk_factors**: Top 2-4 Risiken fuer die KOMMENDE WOCHE. Konkret und aktuell.

11. **overall_sentiment**: bullish, bearish, oder neutral — Ausblick auf die KOMMENDE WOCHE

12. **sentiment_reasoning**: Begruendung des Wochen-Sentiments basierend auf den Wochenend-News
    und dem anstehenden Kalender.

Sei praezise und vorwaertsgerichtet. Der Leser will wissen: Was muss ich HEUTE und DIESE WOCHE beachten?
