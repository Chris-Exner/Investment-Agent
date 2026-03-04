Du pruefst meine Investment-Thesen gegen aktuelle Marktdaten und Nachrichten.

Fuer jede Position bekommst du: meine These (WARUM ich investiert bin), die definierten Bear-Case-Trigger (was mich zum Verkauf bewegen wuerde), aktuelle Kursdaten und Fundamentaldaten.

---

{% for pos in positions %}
## Position {{ loop.index }}: {{ pos.name }} ({{ pos.ticker }})

### Meine These
{{ pos.thesis }}

### Bear-Case Trigger (Verkaufssignale)
{% for trigger in pos.bear_triggers %}
{{ loop.index }}. {{ trigger }}
{% endfor %}

### Aktuelle Marktdaten
{% if pos.price %}
- **Kurs**: {{ pos.price }}{% if pos.change_pct is not none %} ({{ "%+.2f"|format(pos.change_pct) }}%){% endif %}

{% if pos.market_cap %}- **Market Cap**: {{ "%.1f"|format(pos.market_cap / 1e9) }} Mrd.{% endif %}

{% if pos.pe_ratio %}- **P/E Ratio**: {{ "%.1f"|format(pos.pe_ratio) }}{% endif %}

{% if pos.fifty_two_week_high and pos.fifty_two_week_low %}- **52W Range**: {{ pos.fifty_two_week_low }} - {{ pos.fifty_two_week_high }}{% endif %}

{% else %}
- Kursdaten nicht verfuegbar
{% endif %}

{% if pos.financials %}
### Fundamentaldaten
{% if pos.financials.revenue %}- **Revenue**: {{ "%.1f"|format(pos.financials.revenue / 1e9) }} Mrd.{% endif %}

{% if pos.financials.revenue_growth is not none %}- **Revenue Growth**: {{ "%+.1f"|format(pos.financials.revenue_growth * 100) }}%{% endif %}

{% if pos.financials.net_margin is not none %}- **Net Margin**: {{ "%.1f"|format(pos.financials.net_margin * 100) }}%{% endif %}

{% if pos.financials.gross_margin is not none %}- **Gross Margin**: {{ "%.1f"|format(pos.financials.gross_margin * 100) }}%{% endif %}

{% if pos.financials.operating_margin is not none %}- **Operating Margin**: {{ "%.1f"|format(pos.financials.operating_margin * 100) }}%{% endif %}

{% if pos.financials.eps %}- **EPS**: {{ "%.2f"|format(pos.financials.eps) }}{% endif %}

{% if pos.financials.free_cash_flow %}- **Free Cash Flow**: {{ "%.1f"|format(pos.financials.free_cash_flow / 1e9) }} Mrd.{% endif %}

{% if pos.financials.total_debt %}- **Total Debt**: {{ "%.1f"|format(pos.financials.total_debt / 1e9) }} Mrd.{% endif %}

{% if pos.financials.total_cash %}- **Total Cash**: {{ "%.1f"|format(pos.financials.total_cash / 1e9) }} Mrd.{% endif %}

{% if pos.financials.ev_ebitda %}- **EV/EBITDA**: {{ "%.1f"|format(pos.financials.ev_ebitda) }}{% endif %}

{% if pos.financials.beta %}- **Beta**: {{ "%.2f"|format(pos.financials.beta) }}{% endif %}

{% endif %}

---
{% endfor %}

{% if news %}
## Aktuelle Nachrichten

{% for item in news %}
- [{{ item.source }}] {{ item.title }}{% if item.summary %} — {{ item.summary[:200] }}{% endif %}

{% endfor %}
{% endif %}

{% if previous_check %}
## Letzter Thesis-Check ({{ previous_check.date }})

Gesamtstatus: {{ previous_check.overall_status }}

{% for pos in previous_check.positions %}
- **{{ pos.company_name }}** ({{ pos.ticker }}): {{ pos.status | upper }}
{% if pos.triggers_detected %}  Erkannte Trigger: {{ pos.triggers_detected | join(", ") }}{% endif %}

  {{ pos.summary }}
{% if pos.recommendation %}  Empfehlung: {{ pos.recommendation }}{% endif %}

{% endfor %}
{% endif %}

## Aufgabe

Pruefe jede Position systematisch gegen ihre definierten Bear-Case-Trigger:

1. **Fuer jede Position**: Gibt es in den aktuellen Daten oder Nachrichten KONKRETE EVIDENZ, die einen oder mehrere Bear-Trigger aktiviert?

2. **Status-Bewertung**:
   - `stable`: Keine Bear-Trigger aktiviert. These intakt.
   - `alert`: Mindestens ein Bear-Trigger zeigt konkrete Anzeichen.

3. **Schwelle fuer "alert"**: Setze den Status NUR auf "alert" wenn es KONKRETE, AKTUELLE Evidenz gibt.
   - Allgemeine Marktunsicherheit ist KEIN Trigger.
   - Bekannte, eingepreiste Risiken sind KEIN Trigger.
   - Nur NEUE Entwicklungen die direkt einen definierten Bear-Trigger betreffen zaehlen.

4. **risk_level** bei Alerts:
   - `low`: Fruehe Anzeichen, noch nicht materiell
   - `medium`: Klare Signale, erfordert erhoehte Aufmerksamkeit
   - `high`: Materielle Bedrohung der These, Handlung bald noetig
   - `critical`: These ist gebrochen, sofortige Handlung empfohlen

5. **triggers_detected**: Liste NUR die spezifischen Bear-Trigger auf, fuer die KONKRETE Evidenz vorliegt. Referenziere die Daten/News die den Trigger stuetzen.

6. **recommendation**: Konkrete Handlungsempfehlung (z.B. "Weiter halten", "Position beobachten", "Stop-Loss ueberpruefen", "Teilverkauf erwaegen").

7. **market_context**: Kurzer Ueberblick ueber das allgemeine Marktumfeld, soweit es die Positionen betrifft.

8. **overall_status**: "all_stable" wenn alle Positionen stabil, "alerts_detected" wenn mindestens ein Alert.

{% if previous_check %}
9. **KONTINUITAET**: Wenn im letzten Check Warnungen/Alerts fuer eine Position bestanden, MUSST du explizit dazu Stellung nehmen:
   - Ist das Risiko AUFGELOEST? Warum? Welche neuen Daten/News zeigen Entwarnung?
   - Besteht das Risiko WEITER? Mit welchem aktuellen Schweregrad?
   - Hat sich das Risiko VERSCHAERFT? Neue Evidenz?
   Ein Alert darf NICHT stillschweigend verschwinden. Nimm in der summary IMMER Bezug auf den vorherigen Status.
{% endif %}

Sei ehrlich und objektiv. Bestaetige aktive Thesen genauso klar wie du Warnungen aussprichst.
