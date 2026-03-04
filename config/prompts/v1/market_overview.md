Erstelle einen umfassenden Marktüberblick basierend auf den folgenden aktuellen Marktdaten.

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

## Aufgabe

Analysiere die obigen Daten und erstelle einen strukturierten Marktüberblick mit folgenden Abschnitten:

1. **Summary**: 2-3 Sätze Executive Summary der heutigen Marktlage
2. **US Markets**: Analyse der US-Märkte mit Treibern und bemerkenswerten Bewegungen
3. **European Markets**: Analyse der europäischen Märkte
4. **Asian Markets**: Analyse der asiatischen Märkte
5. **Commodities & Forex**: Rohstoff- und Devisenmarkt-Analyse
6. **Macro Outlook**: Makro-Umfeld und Ausblick für die nächsten Tage
7. **Key Events**: Liste der wichtigsten marktbewegenden Ereignisse

Fokussiere auf die "Warum"-Frage: Was treibt die Bewegungen? Welche Zusammenhänge gibt es?
Sei präzise und datengestützt. Vermeide Allgemeinplätze.
