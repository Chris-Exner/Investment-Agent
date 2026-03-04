Erstelle einen umfassenden, kontextreichen Marktueberblick basierend auf den folgenden aktuellen Marktdaten UND Finanznachrichten.

## Aktuelle Indexdaten

{% for stock in indices %}
- **{{ stock.name }}** ({{ stock.ticker }}): {{ stock.price }} ({{ "%+.2f"|format(stock.change_pct) }}%)
{% endfor %}

{% if sectors %}
## Sektorperformance (S&P 500 Sektoren)

{% for sector in sectors %}
- **{{ sector.sector }}**: {{ "%+.2f"|format(sector.change_pct) }}%
{% endfor %}
{% endif %}

{% if commodities %}
## Rohstoffe

{% for stock in commodities %}
- **{{ stock.name }}** ({{ stock.ticker }}): {{ stock.price }} ({{ "%+.2f"|format(stock.change_pct) }}%)
{% endfor %}
{% endif %}

{% if forex %}
## Devisen

{% for stock in forex %}
- **{{ stock.name }}** ({{ stock.ticker }}): {{ stock.price }} ({{ "%+.2f"|format(stock.change_pct) }}%)
{% endfor %}
{% endif %}

{% if macro %}
## Makro-Indikatoren

{% for ind in macro %}
- **{{ ind.name }}**: {{ ind.value }}
{% endfor %}
{% endif %}

{% if news %}
## Aktuelle Finanznachrichten (letzte Stunden)

{% for item in news %}
- [{{ item.source }}] {{ item.title }}{% if item.summary %} -- {{ item.summary[:150] }}{% endif %}
{% endfor %}
{% endif %}

## Aufgabe

Analysiere die obigen Marktdaten UND Nachrichten und erstelle einen strukturierten Marktueberblick.
WICHTIG: Verbinde Datenpunkte mit Nachrichten. Erklaere WARUM sich Maerkte bewegen, nicht nur WIE.

Fuer jeden Abschnitt gelten folgende Anforderungen:

1. **summary**: 3-4 Saetze Executive Summary, die die wichtigsten Marktbewegungen mit ihren URSACHEN verbindet.
   Beispiel: "Die US-Maerkte schlossen nach schwaecher als erwarteten Arbeitsmarktdaten im Plus, da Anleger auf fruehere Zinssenkungen spekulieren."

2. **us_markets**: US-Markt-Analyse mit konkreten Treibern, Sektorrotation, bemerkenswerten Einzelwerten.
   Beziehe dich auf relevante Nachrichten, die US-Maerkte beeinflusst haben.

3. **european_markets**: Europaeische Maerkte mit EZB-Kontext, politischen Entwicklungen, Waehrungseffekten.

4. **asian_markets**: Asiatische Maerkte mit China/Japan/Handelskontext.

5. **commodities_forex**: Rohstoff- und Devisenanalyse mit Angebots-/Nachfragetreibern.
   Gold/Oel: Was treibt den Preis? Dollar-Staerke: Warum?

6. **macro_context**: DAS IST DER WICHTIGSTE ABSCHNITT.
   Verbinde Wirtschaftsdaten (CPI, Jobs, PMI, etc.) mit Zentralbank-Erwartungen (Fed, EZB).
   Sei SPEZIFISCH mit Zahlen und Kausalitaeten.
   Beispiel: "CPI bei 3.5% vs. 3.3% erwartet -> Fed Funds Futures preisen keine Zinssenkung vor September ein -> 10Y Yield steigt auf 4.35%"
   Nutze die Nachrichten, um aktuelle Makro-Entwicklungen einzuordnen.

7. **geopolitical_context**: Geopolitische Faktoren die Maerkte beeinflussen: Handelspolitik, Sanktionen, Konflikte.
   NUR ausfuellen wenn es relevante geopolitische Treiber gibt, sonst leer lassen.

8. **forward_outlook**: Vorausschau fuer die naechsten 1-2 Wochen:
   - Anstehende Wirtschaftsdaten (welche, wann, warum wichtig)
   - Earnings-Saison: Welche Unternehmen berichten
   - Zentralbank-Sitzungen
   - Was koennte die Maerkte bewegen

9. **key_events**: 3-7 spezifische marktbewegende Ereignisse MIT konkretem Impact.
   Beispiel: "CPI bei 3.5% vs. 3.3% erwartet, 10Y Yield auf 4.35% gestiegen"
   NICHT: "CPI-Daten veroeffentlicht" (zu vage)

10. **risk_factors**: Top 2-4 Risikofaktoren, die man im Blick behalten sollte.
    Konkret und aktuell, nicht generisch.

11. **overall_sentiment**: bullish, bearish, oder neutral

12. **sentiment_reasoning**: 1-2 Saetze die das Sentiment begruenden.
    Beispiel: "Neutral trotz positiver Schlusskurse, da die ueberraschend hohe Inflation die Zinssenkungsphantasie daempft."

Sei praezise, datengestuetzt und vermeide Allgemeinplaetze. Jeder Satz sollte Information enthalten.
