Du pruefst am Montagmorgen meine Investment-Thesen im Kontext der Wochenend-Nachrichten.

WICHTIGE REGEL: Die Kursdaten sind FREITAGSSCHLUSSKURSE. Die Wochenend-Nachrichten sind DANACH erschienen. Verbinde die Freitagskurse NICHT kausal mit Wochenend-News. Die Freitagskurse sind VERGANGENHEIT, die Wochenend-News zeigen die ZUKUNFT fuer die kommende Woche.

---

## PRIMAER-INPUT: Wochenend-Nachrichten

{% if news %}
{% for item in news %}
- [{{ item.source }}] {{ item.title }}{% if item.summary %} — {{ item.summary[:200] }}{% endif %}

{% endfor %}
{% else %}
Keine relevanten Wochenend-Nachrichten verfuegbar.
{% endif %}

---

## REFERENZ: Meine Positionen und Freitagsschlusskurse

{% for pos in positions %}
### {{ pos.name }} ({{ pos.ticker }})

**Meine These**: {{ pos.thesis }}

**Bear-Case Trigger**:
{% for trigger in pos.bear_triggers %}
{{ loop.index }}. {{ trigger }}
{% endfor %}

**Freitagsschluss**:
{% if pos.price %}
- Kurs: {{ pos.price }}{% if pos.change_pct is not none %} ({{ "%+.2f"|format(pos.change_pct) }}% Freitag){% endif %}

{% if pos.pe_ratio %}- P/E: {{ "%.1f"|format(pos.pe_ratio) }}{% endif %}

{% if pos.fifty_two_week_high and pos.fifty_two_week_low %}- 52W: {{ pos.fifty_two_week_low }} - {{ pos.fifty_two_week_high }}{% endif %}

{% else %}
- Kursdaten nicht verfuegbar
{% endif %}

{% if pos.financials %}
**Fundamentals**: {% if pos.financials.revenue %}Rev {{ "%.1f"|format(pos.financials.revenue / 1e9) }}B{% endif %}{% if pos.financials.net_margin is not none %}, Net Margin {{ "%.1f"|format(pos.financials.net_margin * 100) }}%{% endif %}{% if pos.financials.free_cash_flow %}, FCF {{ "%.1f"|format(pos.financials.free_cash_flow / 1e9) }}B{% endif %}{% if pos.financials.ev_ebitda %}, EV/EBITDA {{ "%.1f"|format(pos.financials.ev_ebitda) }}{% endif %}

{% endif %}

---
{% endfor %}

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

### 1. Wochenend-News-Impact auf Thesen

Pruefe fuer jede Position: Gibt es in den Wochenend-Nachrichten NEUE Entwicklungen, die einen Bear-Case-Trigger betreffen? Fokus auf vorwaertsgerichtete Implikationen fuer die kommende Woche.

### 2. Wochenvorschau

Fuer jede Position: Welche Termine, Earnings, Events oder Datenpunkte stehen in der kommenden Woche an, die fuer die These relevant sind?

### 3. Status-Bewertung

- `stable`: Keine Wochenend-News betreffen Bear-Trigger. These weiter intakt.
- `alert`: Wochenend-News zeigen konkrete neue Risiken fuer einen oder mehrere Bear-Trigger.

**Schwelle**: Nur "alert" bei NEUEN, KONKRETEN Entwicklungen aus dem Wochenende. Nicht bei bekannten, eingepreisten Risiken.

### 4. Strukturierte Ausgabe

- **triggers_detected**: Nur bei konkreter Evidenz aus Wochenend-News
- **summary**: Pro Position 2-3 Saetze zum Wochenend-Impact + Wochenvorschau
- **recommendation**: Handlungsempfehlung fuer die Woche (z.B. "Earnings am Mittwoch beachten", "Position unveraendert halten")
- **market_context**: Allgemeines Marktumfeld fuer die Woche + wichtigste anstehende Makro-Events

{% if previous_check %}
### 5. KONTINUITAET

Wenn im letzten Check (siehe oben) Warnungen/Alerts fuer eine Position bestanden, MUSST du explizit dazu Stellung nehmen:
- Ist das Risiko AUFGELOEST? Warum? Welche neuen Daten/News zeigen Entwarnung?
- Besteht das Risiko WEITER? Mit welchem aktuellen Schweregrad?
- Hat sich das Risiko VERSCHAERFT? Neue Evidenz?
Ein Alert darf NICHT stillschweigend verschwinden.
{% endif %}

Sei vorwaertsgerichtet: Was bedeuten die Wochenend-News fuer MONTAG und die KOMMENDE WOCHE?
